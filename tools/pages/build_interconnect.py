#!/usr/bin/env python3
"""Regenerate projects/global-interconnect-analysis.html from data/global-interconnect.

    .venv/bin/python tools/pages/build_interconnect.py

PeeringDB is the registry network operators keep about themselves. It lists every
internet exchange point and every colocation facility, and -- the field that
matters -- how many networks are actually present at each.

Counting buildings is the measure that gets quoted and it is the wrong one. The
United States holds 1,376 of the world's 5,861 facilities, 23.48% of them, and
20.04% of the network presences inside them: nine networks per building. The
Netherlands gets 21.5 and Indonesia 20.2, so a Dutch data centre is worth about
two and a half American ones as a place where networks meet.

The second finding is the tail. Of 1,323 registered exchanges, 93 have no
networks on them at all and 69 have exactly one -- 12.24% between them -- and 575
have fewer than ten. The median exchange has twelve networks and the mean has
42.9, which is what a distribution looks like when a handful of exchanges hold
most of the world and the rest hold almost none: the smaller half of all
exchanges account for 5.28% of registered presences.

The third is that the usual account of internet geography is out of date. The
largest exchange in the world is not in Frankfurt, London or Amsterdam. It is
IX.br in Sao Paulo, with 1,860 networks -- 1.83 times DE-CIX Frankfurt and more
than double AMS-IX -- and three of the ten largest are Indonesian.

The empty count is cross-checked. PeeringDB carries a second, independent tally
imported from each exchange's own published member list; four exchanges recorded
as empty by their operator publish a member list showing members, and those are
classed as registry gaps and excluded rather than counted as empty.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-interconnect"
PAGE = "projects/global-interconnect-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def i(v):
    return int(float(v)) if v not in (None, "", "None") else 0


def main():
    ix = rows("gi_exchange")
    cty = rows("gi_country")
    cov = {x["property"]: x["value"] for x in rows("gi_coverage")}
    for x in ix:
        x["net_count"] = i(x["net_count"])
    for c in cty:
        for k in ("exchanges", "empty_exchanges", "single_member_exchanges",
                  "networks_at_exchanges", "largest_exchange_networks",
                  "facilities", "network_presences_in_facilities"):
            c[k] = i(c[k])
    C = {c["iso2"]: c for c in cty}

    ixs = sorted(ix, key=lambda x: -x["net_count"])
    tot_net = sum(x["net_count"] for x in ix)
    empty = [x for x in ix if x["status"] == "empty"]
    single = [x for x in ix if x["status"] == "single member"]
    under10 = [x for x in ix if x["net_count"] < 10]
    med = sorted(x["net_count"] for x in ix)[len(ix) // 2]

    def per(cc):
        c = C[cc]
        return r(1.0 * c["network_presences_in_facilities"] / c["facilities"], 1)

    tot_fac = sum(c["facilities"] for c in cty)
    tot_pres = sum(c["network_presences_in_facilities"] for c in cty)
    big = ixs[0]
    fra = next(x for x in ix if x["name"] == "DE-CIX Frankfurt")
    ams = next(x for x in ix if x["name"] == "AMS-IX")
    lon = next(x for x in ix if x["name"] == "LINX LON1")

    F = dict(
        nix=len(ix), nfac=tot_fac, npres=tot_pres, natix=tot_net,
        ncty=len(cty), cables=i(cov["submarine cables"]),
        landings=i(cov["submarine cable landing points"]),
        lists=i(cov["exchanges publishing a member list"]),
        gap=i(cov["median gap between the two counts"]),
        gaps=i(cov["registry gaps excluded from the empty count"]),
        emptyn=len(empty), singlen=len(single), bothn=len(empty) + len(single),
        bothpct=r(100.0 * (len(empty) + len(single)) / len(ix), 2),
        emptypct=r(100.0 * len(empty) / len(ix), 2),
        inuse=sum(1 for x in ix if x["status"] == "in use"),
        u10=len(under10), u10pct=r(100.0 * len(under10) / len(ix), 1),
        med=med, mean=r(sum(x["net_count"] for x in ix) / float(len(ix)), 1),
        top10=r(100.0 * sum(x["net_count"] for x in ixs[:10]) / tot_net, 2),
        top20=r(100.0 * sum(x["net_count"] for x in ixs[:20]) / tot_net, 2),
        bhalf=r(100.0 * sum(x["net_count"] for x in ixs[len(ixs) // 2:]) / tot_net, 2),
        allempty=sum(1 for c in cty if c["exchanges"] > 0
                     and c["empty_exchanges"] + c["single_member_exchanges"]
                     == c["exchanges"]),
        noix=sum(1 for c in cty if c["exchanges"] == 0),
        bign=big["name"], bigcity=big["city"], bigcc=big["country"],
        bignet=big["net_count"],
        fra=fra["net_count"], ams=ams["net_count"], lon=lon["net_count"],
        ratio=r(1.0 * big["net_count"] / fra["net_count"], 2),
        idtop=sum(1 for x in ixs[:10] if x["country"] == "ID"),
        usfac=C["US"]["facilities"],
        usfacpct=r(100.0 * C["US"]["facilities"] / tot_fac, 2),
        uspres=r(100.0 * C["US"]["network_presences_in_facilities"] / tot_pres, 2),
        usper=per("US"), nlper=per("NL"), idper=per("ID"),
        nlratio=r(per("NL") / per("US"), 2),
        idfac=C["ID"]["facilities"], idpres=C["ID"]["network_presences_in_facilities"],
        phix=C["PH"]["exchanges"], phnet=C["PH"]["networks_at_exchanges"],
        phbig=C["PH"]["largest_exchange_networks"], phfac=C["PH"]["facilities"],
        phper=per("PH"),
    )

    p = Page(PAGE)
    p.relocate(
        "global-water-analysis",
        og_image="og-interconnect.png",
        keywords=["internet exchange point", "PeeringDB", "interconnection",
                  "data centres", "peering", "open data", "data analysis"],
        dataset_name="Internet exchanges and colocation facilities worldwide",
        dataset_desc=("Every registered internet exchange point and colocation "
                      "facility with the number of networks present at each, from "
                      "PeeringDB, with submarine cable landing points from "
                      "TeleGeography"),
        breadcrumb="Where Networks Actually Meet",
        crumb_tail="Interconnection",
        creator="PeeringDB / TeleGeography",
        dataset_url="https://www.peeringdb.com/api/",
        tags=["\U0001f310 Internet", "PeeringDB", "TeleGeography",
              "%s exchanges" % format(F["nix"], ","),
              "<span class=\"dot\"></span> %s facilities" % format(F["nfac"], ",")],
        info=[("Data Sources",
               '<a href="https://www.peeringdb.com/api/" target="_blank" '
               'rel="noopener">PeeringDB</a> &middot; '
               '<a href="https://www.submarinecablemap.com/" target="_blank" '
               'rel="noopener">TeleGeography</a> &middot; '
               '<a href="https://api.worldbank.org/v2/" target="_blank" '
               'rel="noopener">World Bank</a>'),
              ("Coverage",
               "%s exchanges &middot; %s facilities &middot; %s network presences "
               "across %d countries and territories"
               % (format(F["nix"], ","), format(F["nfac"], ","),
                  format(F["npres"], ","), F["ncty"])),
              ("Cross-check",
               "%d exchanges publish their own member list; median disagreement "
               "with the operator's count is %d network(s)" % (F["lists"], F["gap"])),
              ("Licence", "CC BY 4.0 (PeeringDB)")])

    p.head(
        "The Biggest Internet Exchange In The World Is In S&atilde;o Paulo",
        "%s of the world's %s registered internet exchanges have no networks on "
        "them or exactly one. The largest has %s — it is IX.br in São Paulo, %s "
        "times DE-CIX Frankfurt — and a US data centre holds %s networks against "
        "the Netherlands' %s."
        % (F["bothn"], format(F["nix"], ","), format(F["bignet"], ","), F["ratio"],
           F["usper"], F["nlper"]),
        "%s of %s internet exchanges are empty or have one member, and the biggest "
        "one is not in Europe." % (F["bothn"], format(F["nix"], ",")),
        "The Biggest Internet Exchange In The World Is In São Paulo")

    p.hero('''                <h1>The Biggest Internet Exchange In The World Is In S&atilde;o Paulo</h1>
                <p class="{hero_desc}">
                    {nix:,} registered internet exchanges and {nfac:,} colocation
                    facilities, read from the registry operators keep about
                    themselves. Counting buildings is the wrong measure: the
                    United States holds {usfacpct}% of the world&rsquo;s
                    facilities and gets {usper} networks per building, against
                    the Netherlands&rsquo; {nlper}. And {bothn} of the exchanges
                    have no networks on them, or exactly one.
                </p>

                <div class="header-actions">
                    <a href="https://www.peeringdb.com/" target="_blank" class="btn btn-primary">
                        PeeringDB
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="biggest.networks">{bignet:,}</div>
                        <div class="{label}">Networks at IX.br S&atilde;o Paulo, the largest anywhere</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="emptyorsingle.n">{bothn}</div>
                        <div class="{label}">Exchanges with no networks on them, or one</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="median.networks">{med}</div>
                        <div class="{label}">Networks at the median exchange; the mean is {mean}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="nl.over.us">{nlratio}&times;</div>
                        <div class="{label}">Dutch networks per building, against American</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The largest internet exchange in the world is <span data-fact="biggest.name">{bign}</span>, with <span data-fact="biggest.networks">{bignet:,}</span> networks on it &mdash; <span data-fact="biggest.over.frankfurt">{ratio}</span> times DE-CIX Frankfurt&rsquo;s <span data-fact="frankfurt.networks">{fra:,}</span> and more than double AMS-IX&rsquo;s <span data-fact="amsterdam.networks">{ams}</span>. <span data-fact="id.intop10">{idtop}</span> of the ten largest are Indonesian.</p>
                    <ul class="tldr-list">
                        <li>Counting buildings is not counting interconnection. The United States holds <span data-fact="us.facilities">{usfac:,}</span> facilities, <span data-fact="us.facilities.pct">{usfacpct}%</span> of the world&rsquo;s, and <span data-fact="us.presences.pct">{uspres}%</span> of the network presences inside them &mdash; <span data-fact="us.perbuilding">{usper}</span> networks per building against the Netherlands&rsquo; <span data-fact="nl.perbuilding">{nlper}</span> and Indonesia&rsquo;s <span data-fact="id.perbuilding">{idper}</span>.</li>
                        <li><span data-fact="empty.n">{emptyn}</span> of the <span data-fact="gi.exchanges">{nix:,}</span> exchanges have no networks on them at all and <span data-fact="single.n">{singlen}</span> have exactly one: <span data-fact="emptyorsingle.pct">{bothpct}%</span> between them. An exchange with one member is a room with a switch in it.</li>
                        <li>The tail is most of the list. <span data-fact="under10.n">{u10}</span> exchanges &mdash; <span data-fact="under10.pct">{u10pct}%</span> &mdash; have fewer than ten networks, the median has <span data-fact="median.networks">{med}</span> and the mean has <span data-fact="mean.networks">{mean}</span>. The smaller half of all exchanges hold <span data-fact="bottomhalf.pct">{bhalf}%</span> of registered presences between them.</li>
                        <li>The top of the list is short. The twenty largest exchanges carry <span data-fact="top20.pct">{top20}%</span> of every registered presence, and the ten largest carry <span data-fact="top10.pct">{top10}%</span>.</li>
                        <li>The empty count is checked against a second source. <span data-fact="gi.memberlists">{lists}</span> exchanges publish their own machine-readable member list; the median disagreement with the operator&rsquo;s own figure is <span data-fact="gi.gap">{gap}</span> networks, and <span data-fact="gi.registrygaps">{gaps}</span> exchanges recorded as empty do publish members &mdash; those are registry gaps and are excluded from the count above.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "A Building Is Not An Interconnection",
                  "The number that gets quoted is how many data centres a country "
                  "has. The number that decides whether traffic stays local is how "
                  "many networks are inside them. Across {nfac:,} facilities there "
                  "are {npres:,} network presences, and they are not distributed the "
                  "way the buildings are.".format(**F),
                  [("United States", "{v} per building".format(v=F["usper"]),
                    "us.perbuilding",
                    "<span data-fact=\"us.facilities\">{f:,}</span> facilities, "
                    "<span data-fact=\"us.facilities.pct\">{p}%</span> of the "
                    "world&rsquo;s, holding "
                    "<span data-fact=\"us.presences.pct\">{n}%</span> of its network "
                    "presences.".format(f=F["usfac"], p=F["usfacpct"], n=F["uspres"])),
                   ("Netherlands", "{v} per building".format(v=F["nlper"]),
                    "nl.perbuilding",
                    "<span data-fact=\"nl.over.us\">{r}</span> times the American "
                    "figure. A Dutch facility is a different kind of place, not a "
                    "bigger one.".format(r=F["nlratio"])),
                   ("Indonesia", "{v} per building".format(v=F["idper"]),
                    "id.perbuilding",
                    "<span data-fact=\"id.facilities\">{f}</span> facilities holding "
                    "<span data-fact=\"id.presences\">{n:,}</span> presences &mdash; "
                    "a seventh of America&rsquo;s buildings and a third of its "
                    "networks.".format(f=F["idfac"], n=F["idpres"]))],
                  "Facilities against the network presences inside them, for the "
                  "countries with at least forty",
                  "buildingChart"),

        p.section(2, "The Exchanges Nobody Joined",
                  "An internet exchange is a place networks agree to meet. Building "
                  "one is a project with a ribbon; filling it is not. Of the "
                  "{nix:,} registered here, {emptyn} have no networks on them and "
                  "{singlen} have exactly one.".format(**F),
                  [("No networks at all", "{v}".format(v=F["emptyn"]), "empty.n",
                    "<span data-fact=\"empty.pct\">{p}%</span> of every registered "
                    "exchange. Not a low number of members &mdash; none."
                    .format(p=F["emptypct"])),
                   ("Exactly one", "{v}".format(v=F["singlen"]), "single.n",
                    "Together with the empty ones that is "
                    "<span data-fact=\"emptyorsingle.n\">{n}</span> exchanges, "
                    "<span data-fact=\"emptyorsingle.pct\">{p}%</span> of the list. "
                    "One network peering with itself is not an exchange."
                    .format(n=F["bothn"], p=F["bothpct"])),
                   ("Countries with nothing working",
                    "{v}".format(v=F["allempty"]), "allempty.countries",
                    "Countries whose every registered exchange is empty or has a "
                    "single member. A further "
                    "<span data-fact=\"noexchange.countries\">{n}</span> have "
                    "facilities and no exchange at all.".format(n=F["noix"]))],
                  "Every exchange by how many networks are on it",
                  "tailChart"),

        p.section(3, "The Median Exchange Has {med} Networks".format(**F),
                  "The mean is {mean}. When a mean is three and a half times its "
                  "median, the average is describing a handful of places and "
                  "nothing else on the list.".format(**F),
                  [("Under ten networks", "{v}".format(v=F["u10"]), "under10.n",
                    "<span data-fact=\"under10.pct\">{p}%</span> of all exchanges. "
                    "Small enough that what peering saves is unlikely to pay for "
                    "the switch.".format(p=F["u10pct"])),
                   ("The smaller half", "{v}%".format(v=F["bhalf"]),
                    "bottomhalf.pct",
                    "Share of every registered network presence held by the smaller "
                    "half of all exchanges, between them."),
                   ("The twenty largest", "{v}%".format(v=F["top20"]), "top20.pct",
                    "Share held by twenty exchanges. The ten largest hold "
                    "<span data-fact=\"top10.pct\">{t}%</span>."
                    .format(t=F["top10"]))],
                  "Cumulative share of network presences, exchanges ordered largest "
                  "first",
                  "curveChart"),

        p.section(4, "Not Frankfurt, Not London, Not Amsterdam",
                  "The standard account of internet geography names four European "
                  "cities. The registry does not agree: the largest exchange in the "
                  "world is in Brazil, and {idtop} of the ten largest are in "
                  "Indonesia.".format(**F),
                  [(F["bign"], "{v:,}".format(v=F["bignet"]), "biggest.networks",
                    "Networks present, in {c}. That is "
                    "<span data-fact=\"biggest.over.frankfurt\">{r}</span> times "
                    "DE-CIX Frankfurt.".format(c=F["bigcity"], r=F["ratio"])),
                   ("DE-CIX Frankfurt", "{v:,}".format(v=F["fra"]),
                    "frankfurt.networks",
                    "The largest in Europe, against AMS-IX&rsquo;s "
                    "<span data-fact=\"amsterdam.networks\">{a}</span> and LINX "
                    "LON1&rsquo;s <span data-fact=\"london.networks\">{l}</span>."
                    .format(a=F["ams"], l=F["lon"])),
                   ("Indonesian exchanges in the top ten",
                    "{v}".format(v=F["idtop"]), "id.intop10",
                    "Jakarta appears three times in the ten largest exchanges on "
                    "earth, which is not where the usual story puts it.")],
                  "The twelve largest exchanges in the world",
                  "biggestChart"),

        p.section(5, "The Philippines, For Scale",
                  "An archipelago of a hundred and twenty million people, and the "
                  "country this site is mostly about. It has {phix} registered "
                  "exchanges and {phnet} network presences across them.".format(**F),
                  [("Exchanges", "{v}".format(v=F["phix"]), "ph.exchanges",
                    "Holding <span data-fact=\"ph.networks\">{n}</span> network "
                    "presences between them &mdash; fewer than a quarter of what "
                    "sits on IX.br S&atilde;o Paulo alone."
                    .format(n=F["phnet"])),
                   ("Largest exchange", "{v}".format(v=F["phbig"]), "ph.largest",
                    "Networks on the biggest one. The world&rsquo;s largest has "
                    "<span data-fact=\"biggest.networks\">{b:,}</span>."
                    .format(b=F["bignet"])),
                   ("Networks per facility", "{v}".format(v=F["phper"]), "ph.perbuilding",
                    "Across <span data-fact=\"ph.facilities\">{f}</span> facilities "
                    "&mdash; higher than the United States&rsquo; "
                    "<span data-fact=\"us.perbuilding\">{u}</span>, which is a "
                    "reminder that this ratio measures concentration rather than "
                    "capacity.".format(f=F["phfac"], u=F["usper"]))],
                  "Network presences at exchanges, for the twenty countries with the "
                  "most",
                  "countryChart"),

        p.prose(6, "How An Empty Exchange Is Told From A Missing Record",
                "The claim that an exchange has no networks on it is the strongest "
                "one on this page, so it is the one with a second source behind it.",
                [("Two counts of the same thing",
                  "PeeringDB records the number of networks an exchange operator "
                  "says are present, and separately imports a count from the "
                  "exchange's own published member list. %d exchanges publish one. "
                  "Where both exist the median disagreement is %d network, so the "
                  "two track each other closely enough to be used together."
                  % (F["lists"], F["gap"])),
                 ("A gap is not an absence",
                  "%d exchanges are recorded as having no networks by their "
                  "operator while publishing a member list that shows members. "
                  "Those are counted as registry gaps and excluded from the empty "
                  "figure, which is why the number here is %d rather than %d."
                  % (F["gaps"], F["emptyn"], F["emptyn"] + F["gaps"])),
                 ("The registry is self-reported",
                  "PeeringDB is maintained by network operators about themselves. "
                  "A country with no rows may have no exchange, or may have nobody "
                  "filling in the form, and nothing in this data separates those "
                  "two. Every count here is of what is registered.")]),

        p.prose(7, "What These Numbers Are Not",
                "Four limits, each of which would change a conclusion above if "
                "ignored.",
                [("Networks present, not traffic",
                  "A count of networks at an exchange says nothing about how much "
                  "passes over it. Two networks moving a terabit are one row; two "
                  "hundred moving nothing are two hundred. No traffic figure is "
                  "claimed anywhere on this page because the free sources do not "
                  "carry one consistently."),
                 ("Networks per building measures concentration",
                  "It is a ratio of two registered counts, and a high value means "
                  "the networks are gathered in few buildings rather than that the "
                  "buildings are good. The Philippines scores %s and the United "
                  "States %s, which is a fact about how many facilities each has "
                  "rather than about either country's capacity."
                  % (F["phper"], F["usper"])),
                 ("Landing points are counted, not located",
                  "The submarine map contributes %s cables and %s landing points as "
                  "a scale marker. Its landing-point records carry no country code "
                  "and the routes it draws are schematic rather than surveyed, so "
                  "no per-country split and no distance is computed from them."
                  % (format(F["cables"], ","), format(F["landings"], ","))),
                 ("A snapshot, not a series",
                  "PeeringDB records current state, not history, so nothing here "
                  "shows change over time. An exchange that emptied last year and "
                  "one that opened last week look identical.")]),
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
                        <li>The largest internet exchange in the world is
                        <span data-fact="biggest.name">{bign}</span> with
                        <span data-fact="biggest.networks">{bignet:,}</span>
                        networks &mdash;
                        <span data-fact="biggest.over.frankfurt">{ratio}</span>
                        times DE-CIX Frankfurt, and
                        <span data-fact="id.intop10">{idtop}</span> of the ten
                        largest are Indonesian.</li>
                        <li>The United States holds
                        <span data-fact="us.facilities.pct">{usfacpct}%</span> of
                        the world&rsquo;s facilities and
                        <span data-fact="us.presences.pct">{uspres}%</span> of the
                        networks in them:
                        <span data-fact="us.perbuilding">{usper}</span> per
                        building against the Netherlands&rsquo;
                        <span data-fact="nl.perbuilding">{nlper}</span>.</li>
                        <li><span data-fact="empty.n">{emptyn}</span> exchanges have
                        no networks on them and
                        <span data-fact="single.n">{singlen}</span> have one:
                        <span data-fact="emptyorsingle.pct">{bothpct}%</span> of the
                        registered total.</li>
                        <li><span data-fact="under10.n">{u10}</span> exchanges have
                        fewer than ten networks. The median has
                        <span data-fact="median.networks">{med}</span> and the mean
                        has <span data-fact="mean.networks">{mean}</span>.</li>
                        <li>The twenty largest exchanges hold
                        <span data-fact="top20.pct">{top20}%</span> of all registered
                        presences; the smaller half of the list holds
                        <span data-fact="bottomhalf.pct">{bhalf}%</span>.</li>
                        <li>The empty figure is checked against each exchange&rsquo;s
                        own published member list, and
                        <span data-fact="gi.registrygaps">{gaps}</span> apparent
                        empties turned out to be registry gaps rather than empty
                        exchanges.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    # ---- chart data ---------------------------------------------------------
    FB = sorted([c for c in cty if c["facilities"] >= 40],
                key=lambda c: -c["network_presences_in_facilities"])[:18]
    # The first two bars come from status, not from net_count. A raw count of
    # exchanges with zero networks is 97, and the page says 93, because four of
    # them publish a member list and are registry gaps rather than empty
    # exchanges. A chart whose first bar disagreed with the prose beside it would
    # be the page contradicting itself, which is the failure this repo checks for.
    BANDS = [(2, 9, "2-9"), (10, 24, "10-24"), (25, 49, "25-49"),
             (50, 99, "50-99"), (100, 249, "100-249"), (250, 10 ** 9, "250+")]
    LABELS = ["0 (empty)", "0 (registry gap)", "1"] + [b[2] for b in BANDS]
    BC = ([sum(1 for x in ix if x["status"] == "empty"),
           sum(1 for x in ix if x["status"] == "registry gap"),
           sum(1 for x in ix if x["status"] == "single member")]
          + [sum(1 for x in ix if lo <= x["net_count"] <= hi) for lo, hi, _ in BANDS])
    assert sum(BC) == len(ix), "bands drop %d exchanges" % (len(ix) - sum(BC))
    BAR = ["#ef4444", "#a855f7", "#f59e0b"] + ["#3b82f6"] * len(BANDS)
    run, CUM = 0, []
    for x in ixs:
        run += x["net_count"]
        CUM.append(r(100.0 * run / tot_net, 2))
    STEP = [(n, CUM[n - 1]) for n in
            (1, 5, 10, 20, 50, 100, 200, 300, 500, 700, 900, 1100, len(ixs))]
    TOP12 = ixs[:12]
    CN = sorted(cty, key=lambda c: -c["networks_at_exchanges"])[:20]

    charts = ['''        // 01 buildings against the networks inside them. The two bars are on
        //    separate axes on purpose: the point is that their ORDER differs, not
        //    that one is larger.
        new Chart(document.getElementById('buildingChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Facilities', data: %s, order: 2,
                      backgroundColor: 'rgba(148,163,184,0.75)', yAxisID: 'y' },
                    { type: 'line', label: 'Networks per facility', data: %s, order: 1,
                      borderColor: '#22d3ee', backgroundColor: '#22d3ee',
                      pointBackgroundColor: '#22d3ee', pointBorderColor: '#fff',
                      pointBorderWidth: 1, borderWidth: 3, pointRadius: 4,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: {
                    sort: (a, b) => a.datasetIndex - b.datasetIndex } } },
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Facilities' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Networks per facility' } } }
            }
        });''' % (js([c["country"] for c in FB]),
                  js([c["facilities"] for c in FB]),
                  js([r(1.0 * c["network_presences_in_facilities"] / c["facilities"], 1)
                      for c in FB])),

              '''        // 02 the whole population of exchanges by size band. The first two bars
        //    are the finding; the last one is where the internet actually is.
        new Chart(document.getElementById('tailChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Exchanges', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Number of exchanges' } },
                          x: { title: { display: true, text: 'Networks present' } } }
            }
        });''' % (js(LABELS), js(BC), js(BAR)),

              '''        // 03 the concentration curve: exchanges ordered largest first against the
        //    cumulative share of presences they account for.
        new Chart(document.getElementById('curveChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Cumulative %% of network presences', data: %s,
                             borderColor: '#22d3ee', backgroundColor: '#22d3ee',
                             pointBackgroundColor: '#22d3ee',
                             borderWidth: 3, pointRadius: 3, fill: false }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of all presences' } },
                          x: { title: { display: true, text: 'Exchanges, largest first' } } }
            }
        });''' % (js([str(n) for n, _ in STEP]), js([v for _, v in STEP])),

              '''        // 04 the twelve largest. Brazil first, Indonesia three times, and the
        //    European exchanges the story usually leads with in the middle.
        new Chart(document.getElementById('biggestChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Networks present', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Networks present' } } }
            }
        });''' % (js(["%s (%s)" % (x["name"][:34], x["country"]) for x in TOP12]),
                  js([x["net_count"] for x in TOP12]),
                  js(["#22d3ee" if x["country"] == "BR" else
                      ("#f59e0b" if x["country"] == "ID" else "#3b82f6")
                      for x in TOP12])),

              '''        // 05 networks at exchanges by country, which is a different ordering again
        //    from either buildings or presences inside them.
        new Chart(document.getElementById('countryChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Networks at exchanges', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Networks at exchanges' } } }
            }
        });''' % (js([c["country"] for c in CN]),
                  js([c["networks_at_exchanges"] for c in CN]),
                  js(["#22d3ee" if c["iso2"] == "PH" else "#3b82f6" for c in CN])),
    ]

    p.sections(S)
    p.charts(charts)
    p.faq({
        "Which is the largest internet exchange in the world?":
            "%s, in %s, with %s networks present. That is %s times DE-CIX Frankfurt "
            "(%s) and more than double AMS-IX (%s). %d of the ten largest exchanges "
            "are Indonesian. These are counts of networks registered as present, not "
            "of traffic."
            % (F["bign"], F["bigcity"], format(F["bignet"], ","), F["ratio"],
               format(F["fra"], ","), F["ams"], F["idtop"]),
        "How many internet exchanges have no networks on them?":
            "%d of %s registered exchanges have none at all, and %d more have "
            "exactly one -- %s%% between them. The figure is checked against each "
            "exchange's own published member list: %d exchanges publish one, and %d "
            "recorded as empty by their operator do show members, so those are "
            "counted as registry gaps rather than empty exchanges."
            % (F["emptyn"], format(F["nix"], ","), F["singlen"], F["bothpct"],
               F["lists"], F["gaps"]),
        "Does the number of data centres tell you how connected a country is?":
            "No, and the two orderings differ. The United States holds %s facilities, "
            "%s%% of the world's, and %s%% of the network presences inside them -- %s "
            "networks per building, against the Netherlands' %s and Indonesia's %s. "
            "The ratio measures how concentrated the networks are, not how good the "
            "buildings are."
            % (format(F["usfac"], ","), F["usfacpct"], F["uspres"], F["usper"],
               F["nlper"], F["idper"]),
        "How big is a typical internet exchange?":
            "Smaller than the average makes it sound. The median exchange has %d "
            "networks and the mean has %s, because %d exchanges -- %s%% -- have "
            "fewer than ten while the twenty largest carry %s%% of every registered "
            "presence. The smaller half of the whole list accounts for %s%%."
            % (F["med"], F["mean"], F["u10"], F["u10pct"], F["top20"], F["bhalf"]),
        "Where does this interconnection data come from?":
            "PeeringDB, a registry network operators maintain about themselves, "
            "covering %s exchanges and %s colocation facilities across %d countries "
            "and territories, plus %s submarine cables and %s landing points from "
            "TeleGeography as a scale marker. It is free and needs no key. Because "
            "it is self-reported, a country with no rows may have no exchange or may "
            "simply have nobody filling in the form."
            % (format(F["nix"], ","), format(F["nfac"], ","), F["ncty"],
               format(F["cables"], ","), format(F["landings"], ",")),
    })
    p.save(len(S), len(charts))
    blog(F)


BLOG = "blog/global-interconnect-analysis.html"
TITLE = "The World's Biggest Internet Meeting Room Is In Brazil"
DESC = ("There are 1,323 rooms in the world where internet companies meet to swap "
        "traffic. 93 of them have nobody in them at all.")
SUB = "1,323 rooms where networks meet. 93 of them are empty."


def fact(k, v):
    return '<span data-fact="%s">%s</span>' % (k, v)


def blog(F):
    """Write the plain-language companion from the same numbers as the page."""
    import io, re
    src = io.open(BLOG, encoding="utf-8").read()

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, lambda _m: rep, src, count=1)
        if n != 1:
            raise SystemExit("blog: %s matched %d times" % (why, n))

    swap(r"<title>[^<]*</title>",
         "<title>%s | Allan Ni\u00f1al</title>" % TITLE, "title")
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
    src = src.replace("global-water-analysis", "global-interconnect-analysis")
    swap(r'<span class="current">[^<]*</span>',
         '<span class="current">Interconnection</span>', "crumb")
    swap(r'<h1>[^<]*</h1>', "<h1>%s</h1>" % TITLE, "h1")
    swap(r'<p class="subtitle">[^<]*</p>',
         '<p class="subtitle">%s</p>' % SUB, "subtitle")

    a = src.index('<div class="article-content">')
    a = src.index("\n", a) + 1
    b = src.index('                <div class="project-link-box">')
    src = src[:a] + body(F) + src[b:]
    io.open(BLOG, "w", encoding="utf-8").write(src)
    print("rebuilt %s" % BLOG)


def body(F):
    f = fact
    return """                <p>When two internet companies want to swap traffic, they meet in a room.</p>

                <p>The room has a big switch in it. Everyone plugs in. That is called an internet exchange.</p>

                <p>There are {nix} of these rooms in the world.</p>

                <p>{emptyn} of them have nobody in them.</p>

                <div class="stat-callout">
                    <div class="stat-number">{emptyn_f}</div>
                    <div class="stat-label">Rooms with no networks in them at all</div>
                </div>

                <p>Another {singlen} have exactly one. One network in a room by itself is not swapping traffic with anybody.</p>

                <p>So {bothn} rooms are empty or nearly empty. That is {bothpct} per cent of them.</p>

                <h2>Most Rooms Are Small</h2>

                <p>The middle room has {med} networks in it.</p>

                <p>But the average is {mean}. When the average is much bigger than the middle, a few big rooms are pulling it up.</p>

                <p>{u10} rooms have fewer than ten networks. That is {u10pct} per cent of them.</p>

                <p>The smaller half of all the rooms hold {bhalf} per cent of the world's connections between them.</p>

                <p>The twenty biggest hold {top20} per cent.</p>

                <h2>The Biggest One Is Not Where People Say</h2>

                <p>People talk about Frankfurt, London and Amsterdam.</p>

                <p>The biggest room in the world is in Sao Paulo, in Brazil. It has {bignet} networks in it.</p>

                <div class="stat-callout">
                    <div class="stat-number">{bignet_f}</div>
                    <div class="stat-label">Networks in one room in Sao Paulo</div>
                </div>

                <p>Frankfurt has {fra}. So the Brazilian one is {ratio} times bigger.</p>

                <p>Amsterdam has {ams}. London has {lon}.</p>

                <p>And {idtop} of the ten biggest rooms are in Indonesia.</p>

                <h2>Counting Buildings Tells You Nothing</h2>

                <p>People like to count data centres. That is the wrong thing to count.</p>

                <p>The United States has {usfac} of them. That is {usfacpct} per cent of all the ones in the world.</p>

                <p>But only {uspres} per cent of the network connections are in them.</p>

                <p>So each American building holds {usper} networks.</p>

                <p>Each Dutch building holds {nlper}. That is {nlratio} times more.</p>

                <p>Indonesia gets {idper}.</p>

                <p>A building is just a building. What matters is who is inside it.</p>

                <h2>How I Know A Room Is Really Empty</h2>

                <p>I did not want to say a room was empty when it was not.</p>

                <p>Each room's owner writes down how many networks are there. Some rooms also publish their own member list.</p>

                <p>{lists} rooms publish one. I checked the two numbers against each other. The middle gap was {gap} networks, so they mostly agree.</p>

                <p>But {gaps} rooms said they had nobody, while their own list showed members. Those are not empty rooms. Those are rooms that forgot to update a form.</p>

                <p>So I took those {gaps2} out. That is why I say {emptyn2} and not {plusgaps}.</p>

                <h2>Three Things I Cannot Tell You</h2>

                <p>I counted networks, not traffic. Two networks moving a huge amount look smaller here than two hundred networks moving almost nothing.</p>

                <p>The list is written by the companies themselves. If a country has no rooms on the list, maybe it has none. Or maybe nobody filled in the form.</p>

                <p>And this is today, not a story over time. A room that emptied last year looks exactly like a room that opened last week.</p>

""".format(
        nix=f("gi.exchanges", format(F["nix"], ",")),
        emptyn=f("empty.n", F["emptyn"]), emptyn_f=F["emptyn"], emptyn2=F["emptyn"],
        singlen=f("single.n", F["singlen"]),
        bothn=f("emptyorsingle.n", F["bothn"]),
        bothpct=f("emptyorsingle.pct", F["bothpct"]),
        med=f("median.networks", F["med"]), mean=f("mean.networks", F["mean"]),
        u10=f("under10.n", F["u10"]), u10pct=f("under10.pct", F["u10pct"]),
        bhalf=f("bottomhalf.pct", F["bhalf"]), top20=f("top20.pct", F["top20"]),
        bignet=f("biggest.networks", format(F["bignet"], ",")),
        bignet_f=format(F["bignet"], ","),
        fra=f("frankfurt.networks", format(F["fra"], ",")),
        ratio=f("biggest.over.frankfurt", F["ratio"]),
        ams=f("amsterdam.networks", F["ams"]), lon=f("london.networks", F["lon"]),
        idtop=f("id.intop10", F["idtop"]),
        usfac=f("us.facilities", format(F["usfac"], ",")),
        usfacpct=f("us.facilities.pct", F["usfacpct"]),
        uspres=f("us.presences.pct", F["uspres"]),
        usper=f("us.perbuilding", F["usper"]), nlper=f("nl.perbuilding", F["nlper"]),
        nlratio=f("nl.over.us", F["nlratio"]), idper=f("id.perbuilding", F["idper"]),
        lists=f("gi.memberlists", F["lists"]), gap=f("gi.gap", F["gap"]),
        gaps=f("gi.registrygaps", F["gaps"]), gaps2=F["gaps"],
        plusgaps=F["emptyn"] + F["gaps"],
    )


if __name__ == "__main__":
    main()
