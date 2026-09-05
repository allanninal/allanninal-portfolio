#!/usr/bin/env python3
"""What each country reads on Wikipedia, and why "global trends" is a category error.

Two Wikimedia endpoints, no key and no account:

  top-per-country/{ISO}/...   the most-read articles in one country, across every
                              language project, with counts deliberately ROUNDED
                              for privacy (the field is literally views_ceil)
  top/{project}/...           the most-read articles on one language project, with
                              exact counts

The first is the interesting one, and the rounding is the reason it exists: exact
per-country reading figures would be re-identifying, so Wikimedia buckets them.
Every count from that endpoint on this page is therefore approximate by design,
and the page says so rather than presenting a rounded number as a measurement.

The finding this is built to test: there is no such thing as "what the world is
reading today". Take one arbitrary day and the top lists of different countries and
different languages barely intersect -- 15 August 2026 is India's Independence Day,
Hindi Wikipedia's whole top list is about it, and English Wikipedia shows no sign it
is happening.

The second finding is about who owns the world's reference layer. For most of the
non-English countries here, a large share of the most-read articles sit on ENGLISH
Wikipedia rather than on the country's own language project.

Writes:
  gw_country_top.csv      top articles per country per day, with the project
  gw_project_top.csv      top articles per language project per day, exact counts
  gw_country_share.csv    per country: share of its top list that is en.wikipedia
  gw_overlap.csv          pairwise overlap between countries' top lists
  gw_project_overlap.csv  pairwise overlap between language projects
  gw_holiday.csv          the 15 August case study, one row per project
  gw_coverage.csv         what was fetched, what was filtered, and what is rounded
"""
import csv
import datetime
import json
import os
import re
import time
import urllib.error
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(os.path.dirname(__file__), ".cache")
API = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
UA = "allanninal.dev research (https://www.allanninal.dev; one-off analysis)"
SRC = "Wikimedia Analytics pageviews API (CC0)"

# A complete Monday-to-Sunday week, well clear of the reporting lag.
START = datetime.date(2026, 8, 24)
DAYS = 7
# India's Independence Day, kept as a named case study rather than a cherry-pick:
# it sits in its own table and is not mixed into the weekly figures.
HOLIDAY = datetime.date(2026, 8, 15)

TOP_N = 20          # how far down each day's list to read

COUNTRIES = [
    ("US", "United States"), ("GB", "United Kingdom"), ("IN", "India"),
    ("PH", "Philippines"), ("JP", "Japan"), ("DE", "Germany"),
    ("FR", "France"), ("BR", "Brazil"), ("MX", "Mexico"), ("ES", "Spain"),
    ("RU", "Russia"), ("ID", "Indonesia"), ("NG", "Nigeria"), ("EG", "Egypt"),
    ("ZA", "South Africa"), ("KR", "South Korea"), ("VN", "Vietnam"),
    ("TR", "Turkey"), ("IT", "Italy"), ("PL", "Poland"), ("PK", "Pakistan"),
    ("BD", "Bangladesh"), ("TH", "Thailand"), ("AR", "Argentina"),
]

PROJECTS = [
    ("en.wikipedia", "English"), ("es.wikipedia", "Spanish"),
    ("ja.wikipedia", "Japanese"), ("de.wikipedia", "German"),
    ("fr.wikipedia", "French"), ("ru.wikipedia", "Russian"),
    ("pt.wikipedia", "Portuguese"), ("zh.wikipedia", "Chinese"),
    ("ar.wikipedia", "Arabic"), ("id.wikipedia", "Indonesian"),
    ("it.wikipedia", "Italian"), ("pl.wikipedia", "Polish"),
    ("fa.wikipedia", "Persian"), ("hi.wikipedia", "Hindi"),
]

# Navigation and maintenance pages are not reading, and they dominate the raw
# lists: the main page alone is usually the largest single entry in every country.
# Filtering them by pattern does not work. A namespace prefix looks exactly like a
# real article title that happens to contain a colon -- "Special:Search" and
# "Spider-Man: Brand New Day" are the same shape -- and across 98 Wikipedia
# projects there are 288 distinct colon-prefixes, most of them "Special" or
# "Category" in some language and a few of them genuine titles (Spider-Man,
# Avengers, Insidious, Chelovek-pauk).
#
# A regex over letters also fails on Devanagari and similar scripts, because
# Python's \w excludes combining marks, so "Special:Search" in Hindi
# (vishesh:khoj) slipped straight through the first version.
#
# So the namespace names come from MediaWiki itself, per project, via siteinfo.
# That is exact rather than heuristic, it is 98 cached requests, and it is the only
# way to keep "Spider-Man: Brand New Day" while dropping the Vietnamese and Thai
# spellings of Special:Search.
NS_CACHE = {}


def namespaces(project):
    """Namespace names and aliases for one project, from its own API."""
    if project in NS_CACHE:
        return NS_CACHE[project]
    cf = os.path.join(CACHE, "ns_%s.json" % project.replace("/", "_"))
    if os.path.exists(cf):
        names = set(json.load(open(cf)))
    else:
        url = ("https://%s.org/w/api.php?action=query&meta=siteinfo"
               "&siprop=namespaces%%7Cnamespacealiases&format=json" % project)
        names = set()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=45))
            q = d.get("query", {})
            for k, v in q.get("namespaces", {}).items():
                # Every namespace except 0, which is the article namespace and has
                # no prefix. Note "!= 0", not "> 0": Special is namespace -1 and
                # Media is -2, and the first version's "> 0" excluded exactly the
                # two that matter most. Special:Search sailed through as a result.
                if int(k) != 0:
                    for key in ("*", "canonical"):
                        if v.get(key):
                            names.add(v[key].replace(" ", "_"))
            for v in q.get("namespacealiases", []):
                if v.get("*"):
                    names.add(v["*"].replace(" ", "_"))
            time.sleep(0.2)
        except Exception:                                        # noqa: BLE001
            # A project whose API will not answer keeps an empty set: its entries
            # then survive filtering rather than being dropped on a guess, and the
            # count of such projects goes in the coverage file.
            names = set()
        json.dump(sorted(names), open(cf, "w"))
    NS_CACHE[project] = names
    return names


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-26s %6d rows" % (name, len(rows)))


def get(path, key):
    """One cached GET. A 404 is how this API says 'no data for that day'."""
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, key.replace("/", "_") + ".json")
    if os.path.exists(cf):
        return json.load(open(cf))
    url = API + path
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            json.dump(d, open(cf, "w"))
            time.sleep(0.25)          # be a decent client
            return d
        except urllib.error.HTTPError as e:
            if e.code == 404:
                json.dump({"items": []}, open(cf, "w"))
                return {"items": []}
            if attempt == 3:
                raise SystemExit("%s -> HTTP %s" % (url, e.code))
            time.sleep(5 * (attempt + 1))
        except Exception as e:                                  # noqa: BLE001
            if attempt == 3:
                raise SystemExit("%s -> %s" % (url, e))
            time.sleep(5 * (attempt + 1))


def is_article(title, project):
    """True if this is a main-namespace article on this project.

    Main pages are in namespace 0 and so are not caught by the namespace list;
    they are identified by asking the project which page is its main page.
    """
    if ":" in title:
        prefix = title.split(":", 1)[0]
        if prefix in namespaces(project):
            return False
    return title not in main_pages(project) and title != "-"


MAIN_CACHE = {}


def main_pages(project):
    """The titles that are this project's main page, from its own API."""
    if project in MAIN_CACHE:
        return MAIN_CACHE[project]
    cf = os.path.join(CACHE, "mp_%s.json" % project.replace("/", "_"))
    if os.path.exists(cf):
        out = set(json.load(open(cf)))
    else:
        url = ("https://%s.org/w/api.php?action=query&meta=siteinfo"
               "&siprop=general&format=json" % project)
        out = set()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=45))
            mp = d.get("query", {}).get("general", {}).get("mainpage")
            if mp:
                mp = mp.replace(" ", "_")
                out.add(mp)
                # The API gives the full title, e.g. "Wikipedia:Hauptseite", but the
                # pageview lists carry the bare "Hauptseite". Store both.
                if ":" in mp:
                    out.add(mp.split(":", 1)[1])
            time.sleep(0.2)
        except Exception:                                        # noqa: BLE001
            out = set()
        out.add("Main_Page")          # the canonical fallback
        json.dump(sorted(out), open(cf, "w"))
    MAIN_CACHE[project] = out
    return out


def jaccard(a, b):
    return round(100.0 * len(a & b) / len(a | b), 2) if (a or b) else 0.0


def main():
    dates = [START + datetime.timedelta(days=i) for i in range(DAYS)]
    ndropped = 0
    nonwp = 0

    # ---- what each country reads -------------------------------------------
    crows = []
    for iso, name in COUNTRIES:
        got = 0
        for d in dates:
            p = "/top-per-country/%s/all-access/%04d/%02d/%02d" % (
                iso, d.year, d.month, d.day)
            data = get(p, "country_%s_%s" % (iso, d.isoformat()))
            items = data.get("items") or []
            if not items:
                continue
            rank = 0
            for a in items[0].get("articles", []):
                t = a["article"]
                ap = a.get("project", "")
                # Wikipedia only. The per-country endpoint spans every Wikimedia
                # project, and the wiktionary / wikibooks / commons entries in it
                # are almost entirely Special:RecentChanges bot traffic on tiny
                # projects -- not somebody reading an encyclopaedia.
                if ".wikipedia" not in ap:
                    nonwp += 1
                    continue
                if not is_article(t, ap):
                    ndropped += 1
                    continue
                rank += 1
                if rank > TOP_N:
                    break
                got += 1
                crows.append([iso, name, d.isoformat(), rank, t[:120],
                              a.get("project", ""), a.get("views_ceil", ""),
                              "rounded", SRC])
        print("    %-16s %4d entries" % (name, got))
    write("gw_country_top.csv",
          ["country_iso", "country", "date", "rank", "article", "project",
           "views_ceil", "count_basis", "source"], crows)

    # Which countries the API has no data for at all. This is not a fetch failure:
    # the endpoint answers 404 with "the country you asked for is not loaded yet",
    # and the countries it will not answer for are systematically the non-Western
    # ones. It is recorded per country rather than summarised, because a global
    # measurement that silently omits Russia, Egypt, Vietnam, Turkey, Pakistan and
    # Bangladesh is not a global measurement.
    present = {r[0] for r in crows}
    avail = []
    for iso, name in COUNTRIES:
        n = sum(1 for r in crows if r[0] == iso)
        avail.append([iso, name, n,
                      "full" if n >= TOP_N * DAYS else
                      ("none -- API returns 404, country not loaded" if n == 0
                       else "partial -- fewer articles clear the privacy floor"),
                      SRC])
    avail.sort(key=lambda r: (r[2], r[1]))
    write("gw_availability.csv",
          ["country_iso", "country", "entries", "availability", "source"], avail)

    # ---- what each language project reads ----------------------------------
    prows = []
    for proj, lang in PROJECTS:
        for d in dates:
            p = "/top/%s/all-access/%04d/%02d/%02d" % (proj, d.year, d.month, d.day)
            data = get(p, "proj_%s_%s" % (proj, d.isoformat()))
            items = data.get("items") or []
            if not items:
                continue
            rank = 0
            for a in items[0].get("articles", []):
                t = a["article"]
                if not is_article(t, proj):
                    ndropped += 1
                    continue
                rank += 1
                if rank > TOP_N:
                    break
                prows.append([proj, lang, d.isoformat(), rank, t[:120],
                              a.get("views", ""), "exact", SRC])
    write("gw_project_top.csv",
          ["project", "language", "date", "rank", "article", "views",
           "count_basis", "source"], prows)

    # ---- how much of each country's reading is English Wikipedia -----------
    share = []
    for iso, name in COUNTRIES:
        mine = [r for r in crows if r[0] == iso]
        if not mine:
            continue
        en = sum(1 for r in mine if r[5] == "en.wikipedia")
        projs = {}
        for r in mine:
            projs[r[5]] = projs.get(r[5], 0) + 1
        top_proj = max(projs, key=lambda k: projs[k])
        share.append([iso, name, len(mine), en,
                      round(100.0 * en / len(mine), 2),
                      top_proj, projs[top_proj],
                      round(100.0 * projs[top_proj] / len(mine), 2),
                      len(projs), SRC])
    share.sort(key=lambda r: -r[4])
    write("gw_country_share.csv",
          ["country_iso", "country", "entries", "en_wikipedia_entries",
           "en_wikipedia_pct", "top_project", "top_project_entries",
           "top_project_pct", "distinct_projects", "source"], share)

    # ---- overlap between countries -----------------------------------------
    # Jaccard on the SET of articles each country read across the week. A set
    # rather than a ranking, because rank order is noisy day to day and the
    # question is whether the same things are being read at all.
    sets = {iso: {r[4] for r in crows if r[0] == iso} for iso, _ in COUNTRIES}
    orows = []
    for i, (a, an) in enumerate(COUNTRIES):
        for b, bn in COUNTRIES[i + 1:]:
            sa, sb = sets.get(a, set()), sets.get(b, set())
            if not sa or not sb:
                continue
            orows.append([a, an, b, bn, len(sa), len(sb), len(sa & sb),
                          jaccard(sa, sb), SRC])
    orows.sort(key=lambda r: -r[7])
    write("gw_overlap.csv",
          ["a_iso", "a_country", "b_iso", "b_country", "a_articles",
           "b_articles", "shared_articles", "jaccard_pct", "source"], orows)

    # ---- overlap between language projects ---------------------------------
    psets = {p: {r[4] for r in prows if r[0] == p} for p, _ in PROJECTS}
    porows = []
    for i, (a, an) in enumerate(PROJECTS):
        for b, bn in PROJECTS[i + 1:]:
            sa, sb = psets.get(a, set()), psets.get(b, set())
            if not sa or not sb:
                continue
            porows.append([a, an, b, bn, len(sa), len(sb), len(sa & sb),
                           jaccard(sa, sb), SRC])
    porows.sort(key=lambda r: -r[7])
    write("gw_project_overlap.csv",
          ["a_project", "a_language", "b_project", "b_language", "a_articles",
           "b_articles", "shared_articles", "jaccard_pct", "source"], porows)

    # ---- the 15 August case study -------------------------------------------
    hol = []
    for proj, lang in PROJECTS:
        p = "/top/%s/all-access/%04d/%02d/%02d" % (
            proj, HOLIDAY.year, HOLIDAY.month, HOLIDAY.day)
        data = get(p, "proj_%s_%s" % (proj, HOLIDAY.isoformat()))
        items = data.get("items") or []
        if not items:
            continue
        arts = [a for a in items[0].get("articles", [])
                if is_article(a["article"], proj)]
        if not arts:
            continue
        hol.append([proj, lang, HOLIDAY.isoformat(), arts[0]["article"][:120],
                    arts[0].get("views", ""), len(arts), SRC])
    write("gw_holiday.csv",
          ["project", "language", "date", "top_article", "views",
           "articles_after_filter", "source"], hol)

    # ---- coverage ------------------------------------------------------------
    cov = [
        ["countries", len(COUNTRIES), "", SRC],
        ["language projects", len(PROJECTS), "", SRC],
        ["days", DAYS, "%s to %s" % (dates[0], dates[-1]), SRC],
        ["articles read per list", TOP_N, "after filtering", SRC],
        ["country entries kept", len(crows), "", SRC],
        ["project entries kept", len(prows), "", SRC],
        ["non-Wikipedia entries dropped", nonwp,
         "the per-country endpoint spans every Wikimedia project; wiktionary, "
         "wikibooks and commons entries in it are almost entirely "
         "Special:RecentChanges bot traffic on tiny projects", SRC],
        ["namespace entries dropped", ndropped,
         "main pages, searches and namespaced pages. The main page alone is "
         "usually the largest single entry in every country, and keeping it would "
         "make them all look identical for a reason unrelated to interest", SRC],
        ["per-country counts are exact", 0,
         "the API returns views_ceil, deliberately rounded so that per-country "
         "reading cannot re-identify anyone. Every country figure here is "
         "approximate by design", SRC],
        ["per-project counts are exact", 1,
         "the per-project endpoint returns unrounded views", SRC],
        ["bot traffic excluded", 0,
         "all-access includes automated traffic Wikimedia could not classify. A "
         "user-only filter exists per project but not per country, so neither uses "
         "it, for comparability", SRC],
        ["mobile and desktop separated", 0, "all-access combines them", SRC],
        ["reading time or engagement", 0, "a pageview is a request, not a read", SRC],
        ["countries with no data at all",
         sum(1 for iso, _ in COUNTRIES if not any(r[0] == iso for r in crows)),
         "of %d asked for. The API answers 404 with 'the country you asked for is "
         "not loaded yet', and the countries it will not answer for are "
         "systematically the non-Western ones" % len(COUNTRIES), SRC],
        ["countries with a truncated list",
         sum(1 for iso, _ in COUNTRIES
             if 0 < sum(1 for r in crows if r[0] == iso) < TOP_N * DAYS),
         "fewer than %d articles a day clear the privacy floor, so a smaller "
         "country's list is shorter as well as rounder" % TOP_N, SRC],
    ]
    write("gw_coverage.csv", ["property", "value", "note", "source"], cov)
    print("  dropped %d navigation entries" % ndropped)


if __name__ == "__main__":
    main()
