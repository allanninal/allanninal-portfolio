#!/usr/bin/env python3
"""Regenerate projects/housing-analysis.html from data/ph-housing CSVs.

    .venv/bin/python tools/pages/build_housing.py

The published page was titled "Philippine Housing Market Analysis" and led with
an average price of ₱32.8M across 1,500 listings. Both figures are right. The
page built on them was not, for three reasons that only show up once you open
the file:

  * the listings are asking prices scraped from one property portal. None
    carries a date, so the page's growth charts had nothing to be computed from;
  * the mean is 3.57x the median because 103 listings ask ₱100M or more, one of
    them ₱2.5B. "Average price ₱32.8M" describes the advertised luxury tail;
  * coverage is whatever the scraper hit -- 138 listings in Muntinlupa, none in
    most of the Visayas -- so nothing in it is a national figure, and the old
    page's "138 Cities/Areas" metric was Muntinlupa's listing count wearing the
    wrong label. There are 143 city tokens.

Two changes follow. The listings are kept but analysed per square metre of floor
area, which is the only measure that compares a Forbes Park mansion with a
Cavite townhouse -- and doing so collapses the geography almost entirely: 13x on
asking price across the well-covered cities becomes 2.9x per square metre, and
Cabanatuan turns out to be dearer per square metre than Quezon City while
costing a quarter as much per house.

And the page gains a national half it did not have, from the WHO/UNICEF JMP and
IEA/WHO series the World Bank republishes: what share of households have water
they can drink, a toilet that works, power, and a stove that does not fill the
room with smoke. Those have years attached and split urban from rural. The two
halves of the page do not describe the same country, and that is the finding.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-housing"
PAGE = "projects/housing-analysis.html"
MIN_N = 20          # listings with a floor area before a city median is shown


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def peso(v, nd=0):
    return "₱{:,.{nd}f}".format(v, nd=nd)


def mn(v):
    """Pesos as a compact figure, the way the hero cards need them."""
    if v >= 1e9:
        return "₱%.2fB" % (v / 1e9)
    if v >= 1e6:
        return "₱%.1fM" % (v / 1e6)
    return peso(v)


def main():
    lst = rows("ph_housing_listings")
    city = rows("ph_housing_by_city")
    bed = rows("ph_housing_by_bedroom")
    band = rows("ph_housing_price_bands")
    cond = rows("ph_housing_conditions")
    ur = rows("ph_housing_urban_rural")
    asean = rows("ph_housing_asean")

    priced = [x for x in lst if x["price_php"]]
    ps = sorted(f(x["price_php"]) for x in priced)
    fa = sorted(f(x["floor_area_sqm"]) for x in lst if f(x["floor_area_sqm"]))

    def med(xs):
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0

    # cities with enough floor-area listings for a median to mean anything
    wide = [x for x in city if int(x["listings_with_floor_area"]) >= MIN_N]
    wide_psm = sorted(wide, key=lambda x: -f(x["median_price_per_sqm"]))
    wide_price = sorted(wide, key=lambda x: -f(x["median_price_php"]))
    qc = [x for x in city if x["city_token"] == "Quezon City"][0]
    cab = [x for x in city if x["city_token"] == "Cabanatuan"][0]

    def latest(key):
        got = [x for x in cond if x[key]]
        return (int(got[-1]["year"]), f(got[-1][key])) if got else (None, None)

    def svc(name):
        got = [x for x in ur if x["service"] == name]
        return got[-1]

    wy, wsafe = latest("safe_water_pct")
    _, wbasic = latest("basic_water_pct")
    _, sbasic = latest("basic_sanitation_pct")
    _, ssafe = latest("safe_sanitation_pct")
    ey, elec = latest("electricity_pct")
    cy, cook = latest("clean_cooking_pct")
    uy, urban = latest("urban_pop_pct")
    sy, slum = latest("urban_slum_pct")
    y2000 = [x for x in cond if x["year"] == "2000"][0]

    ck, ek, wk, sk = svc("clean_cooking"), svc("electricity"), \
        svc("basic_water"), svc("basic_sanitation")
    ph_a = [x for x in asean if x["country"] == "Philippines"][0]
    others = sorted((x for x in asean if x["country"] != "Philippines"),
                    key=lambda x: f(x["clean_cooking_pct"]))

    F = dict(
        n=len(lst), priced=len(priced), unpriced=len(lst) - len(priced),
        repeats=sum(1 for x in lst if x["occurrence"] == "repeat"),
        cities=len(city),
        mean=r(sum(ps) / len(ps)), median=med(ps),
        mx=max(ps), mnp=min(ps),
        p90=r(ps[int(0.9 * (len(ps) - 1))]), p99=r(ps[int(0.99 * (len(ps) - 1))]),
        over=int([x for x in band if x["band"] == "₱100M and up"][0]["listings"]),
        overpct=f([x for x in band if x["band"] == "₱100M and up"][0]["pct_of_priced"]),
        under6=r(sum(f(x["pct_of_priced"]) for x in band
                     if x["upper_php"] and int(x["upper_php"]) <= 6000000), 2),
        topcity=city[0]["city_token"], topn=int(city[0]["listings"]),
        topmed=f(city[0]["median_price_php"]),
        top3=r(100.0 * sum(int(x["listings"]) for x in city[:3]) / len(lst), 2),
        psm=r(med(sorted(f(x["price_php"]) / f(x["floor_area_sqm"]) for x in lst
                         if x["price_php"] and f(x["floor_area_sqm"])))),
        psmn=sum(1 for x in lst if x["price_php"] and f(x["floor_area_sqm"])),
        famed=med(fa),
        wide=len(wide),
        ptop=wide_psm[0]["city_token"], ptopv=f(wide_psm[0]["median_price_per_sqm"]),
        pbot=wide_psm[-1]["city_token"], pbotv=f(wide_psm[-1]["median_price_per_sqm"]),
        qcpsm=f(qc["median_price_per_sqm"]), qcmed=f(qc["median_price_php"]),
        cabpsm=f(cab["median_price_per_sqm"]), cabmed=f(cab["median_price_php"]),
        bed3=f([x for x in bed if x["bedrooms"] == "3"][0]["median_price_php"]),
        bed3n=int([x for x in bed if x["bedrooms"] == "3"][0]["listings"]),
        wsafe=wsafe, wbasic=wbasic, wy=wy,
        sbasic=sbasic, ssafe=ssafe,
        elec=elec, ey=ey, elec00=f(y2000["electricity_pct"]),
        cook=cook, cy=cy, cook00=f(y2000["clean_cooking_pct"]),
        urban=urban, uy=uy, slum=slum, sy=sy,
        cooku=f(ck["urban_pct"]), cookr=f(ck["rural_pct"]), cookgap=f(ck["gap_pp"]),
        elecgap=f(ek["gap_pp"]), elecr=f(ek["rural_pct"]),
        watergap=f(wk["gap_pp"]),
        sanigap=f(sk["gap_pp"]), saniu=f(sk["urban_pct"]), sanir=f(sk["rural_pct"]),
        ay=int(ph_a["year"]), an=len(asean),
        arank=1 + sum(1 for x in asean
                      if f(x["clean_cooking_pct"]) < f(ph_a["clean_cooking_pct"])),
        anext=others[0]["country"], anextv=f(others[0]["clean_cooking_pct"]),
    )
    F["skew"] = r(F["mean"] / F["median"], 2)
    F["psmspread"] = r(F["ptopv"] / F["pbotv"], 2)
    F["pricespread"] = r(f(wide_price[0]["median_price_php"])
                         / f(wide_price[-1]["median_price_php"]), 2)
    F["qcratio"] = r(F["qcmed"] / F["cabmed"], 2)
    F["cabratio"] = r(F["cabpsm"] / F["qcpsm"], 2)
    F["wgap"] = r(F["wbasic"] - F["wsafe"], 2)
    F["sgap"] = r(F["sbasic"] - F["ssafe"], 2)
    F["cookgain"] = r(F["cook"] - F["cook00"], 2)
    F["aseangap"] = r(F["anextv"] - f(ph_a["clean_cooking_pct"]), 2)
    F["cookph"] = f(ph_a["clean_cooking_pct"])

    T = dict(medianp=peso(F["median"]), meanp=peso(F["mean"]),
             mnm=mn(F["mean"]), mmd=mn(F["median"]), mmx=mn(F["mx"]),
             p90p=mn(F["p90"]), p99p=mn(F["p99"]),
             psmp=peso(F["psm"]), ptopp=peso(F["ptopv"]), pbotp=peso(F["pbotv"]),
             qcp=peso(F["qcpsm"]), cabp=peso(F["cabpsm"]),
             qcmedp=mn(F["qcmed"]), cabmedp=mn(F["cabmed"]),
             topmedp=mn(F["topmed"]), bed3p=mn(F["bed3"]), mnpp=peso(F["mnp"]))

    p = Page(PAGE)
    p.hero('''                <h1>1,500 Asking Prices, And How Filipinos Actually Live</h1>
                <p class="hero-description">
                    Two datasets that do not describe the same country. A portal
                    scrape of {n:,} property listings, median ask {mmd} &mdash; and
                    national figures showing {wsafe}% of households with drinking
                    water that is safely managed and {cook}% cooking on clean fuel.
                </p>

                <div class="header-actions">
                    <a href="https://www.kaggle.com/datasets/klekzee/phillipines-housing-market" target="_blank" class="btn btn-primary">
                        Listing scrape (Kaggle)
                    </a>
                    <a href="https://data.worldbank.org/indicator/SH.H2O.SMDW.ZS" target="_blank" class="btn btn-primary">
                        JMP service levels (World Bank)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="listing.median.m">{mmd}</div>
                        <div class="{label}">Median asking price, {priced:,} priced listings</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="listing.skew">{skew}&times;</div>
                        <div class="{label}">How far the mean sits above that median</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="ph.water.safe">{wsafe}%</div>
                        <div class="{label}">Households with safely managed drinking water, {wy}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="ph.cook">{cook}%</div>
                        <div class="{label}">Relying mainly on clean cooking fuel, {cy}</div>
                    </div>
                </div>
'''.format(**dict(F, **T), **p.t))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The old version of this page led with an average asking price of <span data-fact="listing.mean.m">{mnm}</span>. That figure is arithmetically correct and descriptively useless: the mean is <span data-fact="listing.skew">{skew}</span> times the median because <span data-fact="listing.over100m">{over}</span> of the {priced:,} priced listings ask ₱100M or more, one of them <span data-fact="listing.max.m">{mmx}</span>.</p>
                    <ul class="tldr-list">
                        <li>Per square metre of floor area &mdash; the only measure that compares a Forbes Park mansion with a Cavite townhouse &mdash; the geography almost disappears. Across the <span data-fact="psm.cities">{wide}</span> cities with at least {minn} listings that state a floor area, asking prices span <span data-fact="price.spread">{pricespread}</span>&times; and prices per square metre span <span data-fact="psm.spread">{psmspread}</span>&times;.</li>
                        <li><span data-fact="cab.psm">{cabp}</span> per square metre in Cabanatuan against <span data-fact="qc.psm">{qcp}</span> in Quezon City &mdash; Cabanatuan is <span data-fact="cab.qc.psm.ratio">{cabratio}</span> times dearer per square metre while a whole house there costs a <span data-fact="cab.qc.price.ratio">{qcratio}</span>th of the Quezon City median.</li>
                        <li>Nationally, <span data-fact="ph.water.basic">{wbasic}%</span> of households have basic drinking water and only <span data-fact="ph.water.safe">{wsafe}%</span> have it safely managed &mdash; a <span data-fact="ph.water.gap">{wgap}</span>-point gap between an improved source within half an hour and one on the premises, available when needed, free of contamination.</li>
                        <li>Clean cooking fuel reaches <span data-fact="gap.cook.urban">{cooku}%</span> of urban households and <span data-fact="gap.cook.rural">{cookr}%</span> of rural ones, a <span data-fact="gap.cook">{cookgap}</span>-point gap &mdash; the widest urban-rural split of any service here, and last of <span data-fact="asean.n">{an}</span> in ASEAN.</li>
                        <li>The listings are asking prices with no dates and no weights. Nothing in the first half of this page is a national figure, and no trend can be computed from it.</li>
                    </ul>
'''.format(minn=MIN_N, **dict(F, **T)))

    S = [
        p.section(1, "What The Average Price Is Actually Measuring",
                  "The {priced:,} priced listings distributed across price bands. The "
                  "mean sits in the fifth band; three-quarters of the listings sit "
                  "below it.".format(**F),
                  [("Median ask", T["mmd"], "listing.median.m",
                    "Half the listings ask less than this."),
                   ("Mean ask", T["mnm"], "listing.mean.m",
                    "{s} times the median. The single highest listing asks {m}, and "
                    "{o} ask ₱100M or more.".format(s=F["skew"], m=T["mmx"],
                                                    o=F["over"])),
                   ("Cheapest listing", T["mnpp"], "listing.min",
                    "A check rejects anything below ₱100,000 as a parse failure "
                    "rather than a house; this one is real.")],
                  "Priced listings by asking-price band", "bandChart"),
        p.section(2, "The Geography Is Mostly A Size Difference",
                  "Median asking price and median price per square metre of floor "
                  "area, for the {wide} city tokens with at least {minn} listings "
                  "that state a floor area. The two rankings are barely related."
                  .format(minn=MIN_N, **F),
                  [("Asking-price spread", "{v}&times;".format(v=F["pricespread"]),
                    "price.spread",
                    "Dearest of those {w} cities over cheapest, on median asking "
                    "price.".format(w=F["wide"])),
                   ("Per-square-metre spread", "{v}&times;".format(v=F["psmspread"]),
                    "psm.spread",
                    "The same cities, the same listings, divided by floor area. "
                    "{a} at {av} down to {b} at {bv}.".format(
                        a=F["ptop"], av=T["ptopp"], b=F["pbot"], bv=T["pbotp"])),
                   ("Median floor area", "{v:,.0f} m²".format(v=F["famed"]),
                    "psm.floor.median",
                    "Across every listing that states one. Most of the price gap "
                    "between an expensive city and a cheap one is this number "
                    "changing, not the rate.")],
                  "Median asking price and median price per m², by city",
                  "psmChart"),
        p.section(3, "Cabanatuan Against Quezon City",
                  "One comparison from that chart, on its own, because it is the "
                  "clearest thing in the scrape. Cabanatuan is in Nueva Ecija, about "
                  "a hundred kilometres north of Metro Manila.",
                  [("Quezon City", T["qcmedp"], "qc.median.m",
                    "Median asking price, from {n} listings. Per square metre: "
                    "{p}.".format(n=qc["listings"], p=T["qcp"])),
                   ("Cabanatuan", T["cabmedp"], "cab.median.m",
                    "Median asking price, from {n} listings. Per square metre: "
                    "{p}.".format(n=cab["listings"], p=T["cabp"])),
                   ("Per-square-metre ratio", "{v}&times;".format(v=F["cabratio"]),
                    "cab.qc.psm.ratio",
                    "Cabanatuan over Quezon City. On whole-house price the ratio "
                    "runs the other way, {v} to one. The Quezon City listings are "
                    "not priced at a higher rate; they are bigger."
                    .format(v=F["qcratio"]))],
                  "Median price per m², cities with at least %d floor-area listings"
                  % MIN_N, "cityPsmChart"),
        p.section(4, "Bedrooms, And Where The Sample Runs Out",
                  "Median asking price by bedroom count, with the listing count "
                  "beside it. The medians rise cleanly to six bedrooms; past that "
                  "the counts fall below {minn} and the line starts jumping around "
                  "on two or three listings.".format(minn=MIN_N),
                  [("Three bedrooms", T["bed3p"], "listing.bed3.median.m",
                    "The most common size in the file, {n} listings."
                    .format(n=F["bed3n"])),
                   ("Median per m²", T["psmp"], "listing.psm",
                    "Across the {n:,} listings that state both a price and a floor "
                    "area.".format(n=F["psmn"])),
                   ("Listings with no price", "{v}".format(v=F["unpriced"]),
                    "listing.unpriced",
                    "Excluded from every price figure rather than imputed. "
                    "{r} further listings repeat an earlier row exactly."
                    .format(r=F["repeats"]))],
                  "Median asking price by bedroom count, with listing counts",
                  "bedroomChart"),
        p.section(5, "Basic Access, And Safely Managed Access",
                  "This is where the page leaves the portal. The WHO/UNICEF Joint "
                  "Monitoring Programme grades household water and sanitation in "
                  "tiers, and the distance between two of them is the finding. "
                  "&ldquo;Basic&rdquo; means an improved source within a 30-minute "
                  "round trip. &ldquo;Safely managed&rdquo; means on the premises, "
                  "available when needed, and free of contamination.",
                  [("Basic drinking water", "{v}%".format(v=F["wbasic"]),
                    "ph.water.basic", "Of households, {y}.".format(y=F["wy"])),
                   ("Safely managed", "{v}%".format(v=F["wsafe"]), "ph.water.safe",
                    "The same year. A {g}-point gap, and a check asserts that the "
                    "safely-managed figure never exceeds the basic one, because if "
                    "it did the two indicator codes have been swapped."
                    .format(g=F["wgap"])),
                   ("Sanitation, basic", "{v}%".format(v=F["sbasic"]),
                    "ph.sani.basic",
                    'The same two tiers for toilets: '
                    '<span data-fact="ph.sani.safe">{s}%</span> safely managed, a '
                    '<span data-fact="ph.sani.gap">{g}</span>-point gap.'.format(
                        s=F["ssafe"], g=F["sgap"]))],
                  "Basic and safely managed service levels, 2000 onward",
                  "tierChart"),
        p.section(6, "Urban Against Rural",
                  "The same four services, split. Three of the four favour towns by "
                  "the margin you would expect. The fourth does not, and cooking "
                  "fuel is off the scale of the other three.",
                  [("Clean cooking gap", "{v} pts".format(v=F["cookgap"]),
                    "gap.cook",
                    "{u}% urban against {r}% rural &mdash; the widest split of any "
                    "service here, by a factor of three."
                    .format(u=F["cooku"], r=F["cookr"])),
                   ("Electricity gap", "{v} pts".format(v=F["elecgap"]), "gap.elec",
                    "Rural access is {r}%, so roughly one rural household in nine "
                    "still has no connection.".format(r=F["elecr"])),
                   ("Basic sanitation gap", "{v} pts".format(v=F["sanigap"]),
                    "gap.sani",
                    "Negative: {r}% rural against {u}% urban. The only service on "
                    "this page where the countryside is ahead, and small enough "
                    "that the honest reading is that the two are level."
                    .format(r=F["sanir"], u=F["saniu"]))],
                  "Urban and rural access by service, latest year available",
                  "urbanRuralChart"),
        p.section(7, "Twenty-Five Years Of Wiring And Plumbing",
                  "What has actually moved. Electricity and clean cooking both "
                  "climbed steadily from 2000; the water and sanitation tiers moved "
                  "much less, because the easy part was already done by then.",
                  [("Electricity", "{v}%".format(v=F["elec"]), "ph.elec",
                    'Of households in {y}, up from '
                    '<span data-fact="ph.elec.2000">{a}%</span> in 2000.'.format(
                        y=F["ey"], a=F["elec00"])),
                   ("Clean cooking", "{v}%".format(v=F["cook"]), "ph.cook",
                    'In {y}, up from <span data-fact="ph.cook.2000">{a}%</span> in '
                    '2000 &mdash; a gain of '
                    '<span data-fact="ph.cook.gain">{g}</span> points, and still the '
                    'lowest in ASEAN.'.format(y=F["cy"], a=F["cook00"],
                                              g=F["cookgain"])),
                   ("Urban informal settlement", "{v}%".format(v=F["slum"]),
                    "ph.slum",
                    "Of the urban population, {y}. Published irregularly, so the "
                    "year is stated rather than implied; {u}% of Filipinos lived in "
                    "urban areas in {uy}.".format(y=F["sy"], u=F["urban"],
                                                  uy=F["uy"]))],
                  "Electricity, clean cooking and water access, 2000 onward",
                  "trendChart"),
        p.section(8, "Against The Neighbours",
                  "Clean cooking fuel and basic sanitation across ASEAN-5 and "
                  "Singapore, {ay}. Both are the basic tiers: safely managed "
                  "drinking water is unpublished for Thailand and safely managed "
                  "sanitation for Indonesia, and a six-country chart that quietly "
                  "becomes a five-country chart reads as one that never had the "
                  "sixth.".format(**F),
                  [("Clean cooking rank", "{r} of {n}".format(r=F["arank"],
                                                              n=F["an"]),
                    "asean.rank.cook",
                    "{v}% in the Philippines. Last of the six."
                    .format(v=F["cookph"])),
                   ("Distance to the next country",
                    "{v} pts".format(v=F["aseangap"]), "asean.cook.gap",
                    "{c} is next up at {v}%. The gap to fifth place is wider than "
                    "the gap between second and sixth."
                    .format(c=F["anext"], v=F["anextv"])),
                   ("Basic sanitation rank",
                    "{r} of {n}".format(r=F["arank"], n=F["an"]),
                    "asean.rank.sani",
                    "Also last, at {v}% &mdash; though the six are within thirteen "
                    "points of each other on this measure, which is not true of "
                    "cooking fuel.".format(v=f(ph_a["basic_sanitation_pct"])))],
                  "Clean cooking and basic sanitation, ASEAN-5 and Singapore, %d"
                  % F["ay"], "aseanChart"),
        p.prose(9, "What This Page Does Not Claim",
                "The first half of this page rests on a scrape, and a scrape has "
                "limits that no amount of analysis removes. They are listed here "
                "rather than left to be discovered.",
                [("There is no time dimension",
                  "Not one of the {n:,} listings carries a date. The previous version "
                  "of this page had charts named for growth areas and price-volume "
                  "trends; there is nothing in the file those could have been "
                  "computed from. A check asserts the count of dated listings is "
                  "zero, so a future column cannot quietly turn this into a time "
                  "series.".format(**F)),
                 ("These are asks, not sales",
                  "Every price is what a seller advertised, not what a buyer paid. "
                  "Asking prices in a thin market run above transaction prices by an "
                  "amount this data cannot measure, and the direction of that bias "
                  "is known while its size is not."),
                 ("It is not a sample of anything",
                  "{topn} listings sit in {topcity} and {top3}% of the file sits in "
                  "three city tokens, while most of the Visayas has none. There are "
                  "no survey weights, because a portal's inventory is not a survey. "
                  "Nothing in the first half of this page scales to the "
                  "Philippines.".format(**F)),
                 ("The two halves are not comparable",
                  "The listings describe houses advertised for sale at a median of "
                  "{mmd}. The national figures describe every household, including "
                  "the {slum}% of the urban population in informal settlements. "
                  "Nothing here connects an asking price to a service level, and "
                  "the page does not try.".format(slum=F["slum"], **T)),
                 ("What a real house price index would need",
                  "Dated transactions, a consistent basket, and geographic weights. "
                  "BSP publishes a residential real estate price index built on bank "
                  "loan data; it is not in this analysis because bsp.gov.ph is not "
                  "reachable from a script here. That is a gap, and naming it is "
                  "better than filling it with a scrape.")]),
        p.prose(10, "Method",
                "One fetcher, eight CSVs, two sources that are kept visibly apart.",
                [("The scrape is downloaded, not committed",
                  "The Kaggle mirror serves the archive without authentication. The "
                  "fetcher unzips it in memory and writes the cleaned listings plus "
                  "the derived tables. Two CSVs ship inside that archive and they are "
                  "the same rows twice; merging them would double every listing, so "
                  "only one is read."),
                 ("Per square metre is the comparable measure",
                  "Median price per square metre of floor area, computed per listing "
                  "and then medianed, on the {psmn:,} listings that state both. City "
                  "medians are shown only above {minn} such listings, because below "
                  "that the median moves on one house.".format(minn=MIN_N, **F)),
                 ("Two outliers turned out to be real",
                  "A check bounding price per square metre first failed on a ₱250M "
                  "beachfront villa on Siargao at ₱1.25M per square metre and a "
                  "₱300,000 installment house in Pagadian at ₱3,750. Both are "
                  "genuine listings; the bounds were wrong and were widened to catch "
                  "only a unit error. The 333&times; spread between them is now "
                  "recorded as a warning rather than hidden."),
                 ("Coverage is written to a CSV",
                  "ph_housing_coverage.csv records what the scrape reaches and what "
                  "it does not, one row per property, including the three zeroes "
                  "that matter: no dated listings, no transaction prices, no survey "
                  "weights. Coverage that lives only in a log is coverage nobody can "
                  "audit."),
                 ("The national half comes through the World Bank",
                  "WHO/UNICEF JMP service levels and IEA/WHO clean cooking access, "
                  "fetched from the World Bank WDI API rather than from the "
                  "originating agencies, because that API is reachable and returns a "
                  "clean error on a wrong indicator code instead of an empty "
                  "success."),
                 ("Tier ordering is asserted, not assumed",
                  "A check fails if safely-managed access ever exceeds basic access "
                  "for water or sanitation. Safely managed is a strict subset of "
                  "basic, so a crossing would mean two indicator codes had been "
                  "swapped &mdash; which is not the kind of mistake that looks wrong "
                  "on a chart.")]),
    ]

    S.append('''        <section class="{wrap}">
            <div class="container">
                <div class="section-header fade-up">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>The <span data-fact="listing.mean.m">{mnm}</span> average
                        asking price this page used to lead with is
                        <span data-fact="listing.skew">{skew}</span> times the median
                        of <span data-fact="listing.median.m">{mmd}</span>, because
                        <span data-fact="listing.over100m">{over}</span> of
                        {priced:,} priced listings ask ₱100M or more.</li>
                        <li>Per square metre of floor area the geography nearly
                        vanishes: <span data-fact="price.spread">{pricespread}</span>&times;
                        on asking price across the well-covered cities becomes
                        <span data-fact="psm.spread">{psmspread}</span>&times; per
                        square metre. Cabanatuan at
                        <span data-fact="cab.psm">{cabp}</span> is dearer than Quezon
                        City at <span data-fact="qc.psm">{qcp}</span>.</li>
                        <li><span data-fact="ph.water.basic">{wbasic}%</span> of
                        households have basic drinking water; only
                        <span data-fact="ph.water.safe">{wsafe}%</span> have it safely
                        managed &mdash; a
                        <span data-fact="ph.water.gap">{wgap}</span>-point gap.</li>
                        <li>Clean cooking fuel reaches
                        <span data-fact="gap.cook.urban">{cooku}%</span> of urban and
                        <span data-fact="gap.cook.rural">{cookr}%</span> of rural
                        households, a <span data-fact="gap.cook">{cookgap}</span>-point
                        gap, and ranks
                        <span data-fact="asean.rank.cook">{arank}</span> of
                        <span data-fact="asean.n">{an}</span> in ASEAN &mdash;
                        <span data-fact="asean.cook.gap">{aseangap}</span> points
                        behind {anext}.</li>
                        <li>Basic sanitation is the one service where rural
                        (<span data-fact="gap.sani.rural">{sanir}%</span>) edges urban
                        (<span data-fact="gap.sani.urban">{saniu}%</span>), by
                        <span data-fact="gap.sani">{sanigap}</span> points.</li>
                        <li>The listings carry no dates, no transaction prices and no
                        survey weights. Nothing in the first half of this page is a
                        national figure.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**dict(F, **T), **p.t))

    BAND = [x for x in band]
    W = wide_psm
    BEDS = [x for x in bed]
    C = [x for x in cond if x["year"] >= "2000"]

    charts = ['''        // 01 asking-price bands. The mean lands in the fifth band, which is the
        //    point of the chart.
        new Chart(document.getElementById('bandChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Listings', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of priced listings'; } } } },
                scales: { x: { title: { display: true, text: 'Asking-price band' } },
                          y: { beginAtZero: true,
                               title: { display: true, text: 'Listings' } } }
            }
        });''' % (js([x["band"] for x in BAND]),
                  js([int(x["listings"]) for x in BAND]),
                  js(["#ef4444" if x["band"] == "₱100M and up" else "#3b82f6"
                      for x in BAND]),
                  js([f(x["pct_of_priced"]) for x in BAND])),

              '''        // 02 the same cities ranked two ways. Two y axes because the units differ
        //    by three orders of magnitude; the shape mismatch is the finding.
        new Chart(document.getElementById('psmChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Median asking price (PHP)', data: %s,
                      backgroundColor: 'rgba(59,130,246,0.65)', yAxisID: 'y' },
                    { type: 'line', label: 'Median price per m² (PHP)', data: %s,
                      borderColor: '#f59e0b', borderWidth: 3, pointRadius: 4,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Median asking price (PHP)' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'PHP per m²' } } }
            }
        });''' % (js([x["city_token"] for x in wide_price]),
                  js([f(x["median_price_php"]) for x in wide_price]),
                  js([f(x["median_price_per_sqm"]) for x in wide_price])),

              '''        // 03 price per m² alone, ranked. Metro Manila cities are highlighted so the
        //    absence of a pattern is visible rather than asserted.
        new Chart(document.getElementById('cityPsmChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Median PHP per m²', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'PHP per m² of floor area' } } }
            }
        });''' % (js([x["city_token"] for x in W]),
                  js([f(x["median_price_per_sqm"]) for x in W]),
                  js(["#8b5cf6" if x["city_token"] in NCR else "#22c55e"
                      for x in W])),

              '''        // 04 bedroom medians with counts. Above six bedrooms the counts collapse and
        //    the medians are noise; the count series is drawn so that is visible.
        new Chart(document.getElementById('bedroomChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Median asking price (PHP)', data: %s,
                      backgroundColor: %s, yAxisID: 'y' },
                    { type: 'line', label: 'Listings', data: %s,
                      borderColor: '#64748b', borderWidth: 2, pointRadius: 3,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { x: { title: { display: true, text: 'Bedrooms' } },
                          y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Median asking price (PHP)' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Listings' } } }
            }
        });''' % (js([x["bedrooms"] for x in BEDS]),
                  js([f(x["median_price_php"]) for x in BEDS]),
                  js(["#3b82f6" if int(x["listings"]) >= MIN_N else "#cbd5e1"
                      for x in BEDS]),
                  js([int(x["listings"]) for x in BEDS])),

              '''        // 05 basic against safely managed. The vertical distance between each pair
        //    is what the section is about.
        new Chart(document.getElementById('tierChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Drinking water, basic (%%)', data: %s,
                      borderColor: '#3b82f6', borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Drinking water, safely managed (%%)', data: %s,
                      borderColor: '#3b82f6', borderDash: [6, 4], borderWidth: 3,
                      pointRadius: 0, fill: false },
                    { label: 'Sanitation, basic (%%)', data: %s,
                      borderColor: '#f59e0b', borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Sanitation, safely managed (%%)', data: %s,
                      borderColor: '#f59e0b', borderDash: [6, 4], borderWidth: 3,
                      pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: '%% of households' } } }
            }
        });''' % (js([x["year"] for x in C]),
                  js([f(x["basic_water_pct"]) for x in C]),
                  js([f(x["safe_water_pct"]) for x in C]),
                  js([f(x["basic_sanitation_pct"]) for x in C]),
                  js([f(x["safe_sanitation_pct"]) for x in C])),

              '''        // 06 urban against rural, four services. Cooking fuel is the outlier and
        //    sanitation is the sign flip.
        new Chart(document.getElementById('urbanRuralChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Urban (%%)', data: %s, backgroundColor: '#8b5cf6' },
                    { label: 'Rural (%%)', data: %s, backgroundColor: '#22c55e' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { tooltip: { callbacks: { afterBody: function (c) {
                    return 'Gap: ' + %s[c[0].dataIndex] + ' points'; } } } },
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: '%% of population' } } }
            }
        });''' % (js(["%s (%s)" % (LBL[x["service"]], x["year"]) for x in GAPS]),
                  js([f(x["urban_pct"]) for x in GAPS]),
                  js([f(x["rural_pct"]) for x in GAPS]),
                  js([f(x["gap_pp"]) for x in GAPS])),

              '''        // 07 what actually moved since 2000.
        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Electricity (%%)', data: %s, borderColor: '#f59e0b',
                      borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Clean cooking fuel (%%)', data: %s, borderColor: '#ef4444',
                      borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Safely managed water (%%)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 3, pointRadius: 0, fill: false },
                    { label: 'Urban population share (%%)', data: %s,
                      borderColor: '#94a3b8', borderDash: [4, 4], borderWidth: 2,
                      pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: '%% of population' } } }
            }
        });''' % (js([x["year"] for x in C]),
                  js([f(x["electricity_pct"]) for x in C]),
                  js([f(x["clean_cooking_pct"]) for x in C]),
                  js([f(x["safe_water_pct"]) for x in C]),
                  js([f(x["urban_pop_pct"]) for x in C])),

              '''        // 08 ASEAN, both basic tiers. The Philippines is last on each; the cooking
        //    gap to fifth place is the one that is unusual.
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Clean cooking fuel (%%)', data: %s, backgroundColor: %s },
                    { label: 'Basic sanitation (%%)', data: %s,
                      backgroundColor: 'rgba(148,163,184,0.55)' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: '%% of population' } } }
            }
        });''' % (js([x["country"] for x in asean]),
                  js([f(x["clean_cooking_pct"]) for x in asean]),
                  js(["#ef4444" if x["country"] == "Philippines" else "#3b82f6"
                      for x in asean]),
                  js([f(x["basic_sanitation_pct"]) for x in asean])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "1,500 Asking Prices, And How Filipinos Actually Live",
        "A portal scrape of %s Philippine property listings analysed per square "
        "metre, where a %sx spread in asking price becomes %sx, set against "
        "national WHO/UNICEF JMP figures: %s%% of households have basic drinking "
        "water and %s%% have it safely managed."
        % (format(F["n"], ","), F["pricespread"], F["psmspread"], F["wbasic"],
           F["wsafe"]),
        "The average asking price is %s times the median. Per square metre the "
        "geography nearly vanishes." % F["skew"],
        "1,500 Asking Prices, And How Filipinos Actually Live")
    p.faq({
        "What is the average house price in the Philippines?":
            "There is no reliable answer from this data, and the question is the "
            "problem. In a scrape of %s listings the mean asking price is %s and the "
            "median is %s -- the mean is %s times higher because %d listings ask ₱100 "
            "million or more and one asks %s. These are asking prices from one "
            "property portal, undated and unweighted, so neither figure describes the "
            "Philippines."
            % (format(F["n"], ","), peso(F["mean"]), peso(F["median"]), F["skew"],
               F["over"], peso(F["mx"])),
        "Is property in Metro Manila more expensive per square metre than in the provinces?":
            "Much less than the headline prices suggest. Across the %d city tokens "
            "with at least %d listings that state a floor area, median asking prices "
            "span %sx and median prices per square metre span only %sx. Cabanatuan in "
            "Nueva Ecija runs %s per square metre against Quezon City's %s -- dearer "
            "per square metre, while a whole house there costs a %sth as much. Most of "
            "the price gap between an expensive city and a cheap one is a difference "
            "in floor area, not in rate."
            % (F["wide"], MIN_N, F["pricespread"], F["psmspread"], peso(F["cabpsm"]),
               peso(F["qcpsm"]), F["qcratio"]),
        "How many Filipino households have safe drinking water?":
            "%s%% had basic drinking water in %d and %s%% had it safely managed -- a "
            "%s-point gap. Basic means an improved source within a 30-minute round "
            "trip; safely managed means on the premises, available when needed and "
            "free of contamination. For sanitation the two tiers are %s%% and %s%%."
            % (F["wbasic"], F["wy"], F["wsafe"], F["wgap"], F["sbasic"], F["ssafe"]),
        "How many Filipino households cook with clean fuel?":
            "%s%% in %d, up from %s%% in 2000. The urban-rural split is the widest of "
            "any service here: %s%% of urban households against %s%% of rural ones, a "
            "%s-point gap. Among ASEAN-5 and Singapore the Philippines ranks last, %s "
            "points behind %s."
            % (F["cook"], F["cy"], F["cook00"], F["cooku"], F["cookr"], F["cookgap"],
               F["aseangap"], F["anext"]),
        "Can you compute Philippine house price trends from this data?":
            "No. Not one of the %s listings carries a date, so there is no time "
            "dimension to compute a trend from, and a check asserts that count stays "
            "at zero. BSP publishes a residential real estate price index built on "
            "bank loan data, which is the right source for a trend; bsp.gov.ph is not "
            "reachable from a script here, so it is named as a gap rather than "
            "substituted for." % format(F["n"], ","),
    })
    p.save(len(S), len(charts))


NCR = {"Quezon City", "Manila", "Makati", "Pasig", "Taguig", "Paranaque",
       "Las Pinas", "Muntinlupa", "Marikina", "Caloocan", "Mandaluyong",
       "Malabon", "Navotas", "Valenzuela", "San Juan", "Pasay", "Pateros"}
LBL = {"basic_water": "Basic drinking water", "basic_sanitation": "Basic sanitation",
       "electricity": "Electricity", "clean_cooking": "Clean cooking fuel"}
GAPS = []


if __name__ == "__main__":
    GAPS[:] = []
    _ur = list(csv.DictReader(open(os.path.join(D, "ph_housing_urban_rural.csv"))))
    for _s in ("basic_water", "basic_sanitation", "electricity", "clean_cooking"):
        GAPS.append([x for x in _ur if x["service"] == _s][-1])
    main()
