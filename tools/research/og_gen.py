#!/usr/bin/env python3
"""Render 1200x630 Open Graph cards for blog posts, matching the Feb 2026 design.

Usage: og_gen.py <outdir>
Renders via headless Chrome so typography matches the site's own webfonts.
"""
import os
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:1200px; height:630px; background:#0b0f19; overflow:hidden;
         font-family:Inter,-apple-system,Helvetica,sans-serif; -webkit-font-smoothing:antialiased; }}
  .glow {{ position:absolute; inset:0;
    background:
      radial-gradient(circle at 10% 16%, rgba(59,130,246,.085) 0%, transparent 38%),
      radial-gradient(circle at 90% 84%, rgba(139,92,246,.065) 0%, transparent 38%),
      radial-gradient(circle at 50% 50%, rgba(6,182,212,.025) 0%, transparent 50%); }}
  .wrap {{ position:relative; padding:55px 70px; height:100%; }}
  .icon {{ width:72px; height:72px; border-radius:18px; background:#182236;
    border:1px solid #1e293b; display:flex; align-items:center; justify-content:center;
    font-size:36px; line-height:1; }}
  .pill {{ display:inline-block; margin-top:26px; padding:5px 11px 6px;
    background:rgba(59,130,246,.15); color:#3b82f6; font-size:13px; font-weight:600;
    border-radius:6px 6px 0 0; border-bottom:3px solid #3b82f6; }}
  h1 {{ margin-top:28px; font-size:{tsize}px; font-weight:500; letter-spacing:-.02em;
    color:#f1f5f9; line-height:1.12; max-width:1010px; }}
  .sub {{ margin-top:14px; font-size:20px; color:#94a3b8; line-height:1.45; max-width:900px; }}
  .stats {{ display:flex; gap:56px; margin-top:34px; }}
  .stat .n {{ font-family:'JetBrains Mono',ui-monospace,monospace; font-size:34px;
    font-weight:500; color:#3b82f6; letter-spacing:.01em; }}
  .stat .l {{ margin-top:5px; font-size:12px; letter-spacing:.09em; text-transform:uppercase;
    color:#64748b; font-weight:500; }}
  .author {{ position:absolute; left:70px; bottom:48px; display:flex; align-items:center; gap:16px; }}
  .av {{ width:48px; height:48px; border-radius:50%; background:#123354; color:#60a5fa;
    display:flex; align-items:center; justify-content:center; font-size:15px; font-weight:600;
    letter-spacing:.03em; }}
  .who {{ color:#f1f5f9; font-size:17px; font-weight:500; }}
  .role {{ color:#64748b; font-size:13px; margin-top:2px; }}
  .bars {{ position:absolute; right:70px; bottom:42px; display:flex; align-items:flex-end; gap:8px; height:105px; }}
  .bars i {{ display:block; width:21px; border-radius:4px 4px 0 0; }}
</style></head><body>
<div class="glow"></div>
<div class="wrap">
  <div class="icon">{icon}</div>
  <div><span class="pill">{pill}</span></div>
  <h1>{title}</h1>
  <div class="sub">{sub}</div>
  <div class="stats">{stats}</div>
  <div class="author">
    <div class="av">AN</div>
    <div><div class="who">Allan Ni&ntilde;al</div><div class="role">Data &amp; AI Engineer</div></div>
  </div>
  <div class="bars">{bars}</div>
</div></body></html>"""

BARS = [(44, "#1d4ed8"), (62, "#2563eb"), (78, "#3b82f6"),
        (93, "#3b82f6"), (84, "#3b82f6"), (60, "#2f7ae5"), (50, "#2f7ae5")]


def render(spec, outdir):
    stats = "".join(
        '<div class="stat"><div class="n">%s</div><div class="l">%s</div></div>' % (n, l)
        for n, l in spec["stats"])
    bars = "".join('<i style="height:%dpx;background:%s"></i>' % (h, c) for h, c in BARS)
    html = TPL.format(icon=spec["icon"], pill=spec["pill"], title=spec["title"],
                      sub=spec["sub"], stats=stats, bars=bars,
                      tsize=spec.get("tsize", 48))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        src = f.name
    out = os.path.join(outdir, spec["file"])
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=4000",
                    "--screenshot=" + out, "--window-size=1200,630", src],
                   check=True, capture_output=True)
    os.unlink(src)
    # match the ~32KB weight of the existing cards: palette PNG, no dithering
    # (dithering adds noise that inflates the file; the gradient is smooth enough
    #  at 128 colours that no banding shows)
    subprocess.run(["magick", out, "-strip", "+dither", "-colors", "128",
                    "PNG8:" + out], check=True, capture_output=True)
    return out


SPECS = [
    dict(file="og-cebu-logistics.png", icon="&#128674;", pill="Logistics Data",
         title="Cebu Port &amp; Road Network",
         sub="Cargo, containers, passengers, and the roads behind the piers",
         stats=[("71.9M", "Metric Tons"), ("55.8%", "RoRo Cargo"), ("CPA", "Source")]),
    dict(file="og-dengue.png", icon="&#129439;", pill="Health Data",
         title="Philippine Dengue Surveillance",
         sub="Eleven years of cases, deaths, seasonality, and geography",
         stats=[("442K", "Peak Cases"), ("81", "Provinces"), ("DOH", "Source")]),
    dict(file="og-tourism.png", icon="&#9992;&#65039;", pill="Tourism Data",
         title="Philippine Visitor Arrivals",
         sub="Sixteen years of arrivals, collapse, recovery, and a new top market",
         stats=[("6.48M", "2025 Arrivals"), ("16", "Years"), ("DOT", "Source")]),
    dict(file="og-trade.png", icon="&#128230;", pill="Trade Data",
         title="Philippine Foreign Trade",
         sub="A decade of imports, exports, and a deficit that never closes",
         stats=[("$200.9B", "Total Trade"), ("53.4%", "Electronics"), ("WITS", "Source")]),
    dict(file="og-rice-prices.png", icon="&#127823;", pill="Food Prices",
         title="Philippine Rice Prices",
         sub="Twenty-six years from the farm gate to the shelf",
         stats=[("2.9&times;", "Since 2000"), ("21%", "Retail Margin 2020"), ("WFP+DA", "Source")]),
    dict(file="og-electricity.png", icon="&#9889;", pill="Energy",
         title="Philippine Electricity",
         sub="The most coal-dependent grid in Southeast Asia",
         stats=[("58.7%", "Coal Share 2025"), ("P14.78", "Meralco /kWh"), ("Ember", "Source")]),
    dict(file="og-earthquake.png", icon="&#127755;", pill="Seismic Data",
         title="Philippine Earthquakes 2000&ndash;2026",
         sub="Every M4.5+ event in the USGS catalogue &mdash; and the threshold below which it stops being usable",
         stats=[("9,203", "Events M4.5+"), ("M7.8", "Strongest"), ("USGS", "Source")]),
    dict(file="og-covid.png", icon="&#129440;", pill="Health Data",
         title="Philippine COVID-19 2020&ndash;2026",
         sub="Confirmed deaths against excess deaths, and what the case fatality rate leaves out",
         stats=[("66,864", "Confirmed Deaths"), ("290,774", "Excess Deaths"), ("OWID", "Source")]),
    dict(file="og-internet.png", icon="&#128225;", pill="Connectivity",
         title="Philippine Internet 2000&ndash;2025",
         sub="Speeds up 9.2&times; in six years, and still last in ASEAN for who is online",
         stats=[("150 Mbps", "Fixed, 2025Q3"), ("6 of 6", "ASEAN Access Rank"), ("WB+Ookla", "Source")]),
    dict(file="og-agriculture.png", icon="&#127806;", pill="Agriculture",
         title="Philippine Agriculture 1961&ndash;2024",
         sub="Rice output up 4.9&times; on barely more land &mdash; and still behind the region per hectare",
         stats=[("19.09M t", "Rice, 2024"), ("33%", "Behind Vietnam"), ("FAOSTAT", "Source")]),
    dict(file="og-election.png", icon="&#128499;&#65039;", pill="Elections",
         title="The 2022 Philippine Election",
         sub="The margin, and the two million ballots that named no president",
         stats=[("82.98%", "Turnout"), ("2,213,371", "Invalid Ballots"), ("Canvass", "Source")]),
    dict(file="og-budget.png", icon="&#127974;", pill="Public Finance",
         title="Philippine Public Finances",
         sub="Debt and its cost are both below their 1990s levels &mdash; and both have turned back up",
         stats=[("56.6%", "Debt / GDP"), ("15.3%", "Spending on Interest"), ("WB+IMF", "Source")]),
    dict(file="og-social-media.png", icon="&#128172;", pill="NLP / Text",
         title="Inside a Filipino Hate-Speech Corpus",
         sub="27,383 labelled posts, opened and measured &mdash; with none of the text reproduced",
         stats=[("273", "Posts Leaking"), ("79%", "Under 140 Chars"), ("HuggingFace", "Source")]),
    dict(file="og-transit.png", icon="&#128652;", pill="Transit / OSM",
         title="What Metro Manila&rsquo;s Transit Map Leaves Out",
         sub="803 bus routes mapped, 26 jeepney routes &mdash; the gap is the finding",
         stats=[("803", "Bus Routes"), ("26", "Jeepney Routes"), ("OSM", "Source")]),
    dict(file="og-competitiveness.png", icon="&#128666;", pill="Logistics",
         title="How Well Do Goods Actually Move?",
         sub="Philippine logistics on the World Bank LPI &mdash; on time, then stuck at the border",
         stats=[("3.3 / 5", "Overall LPI"), ("2.8", "Customs"), ("World Bank", "Source")]),
    dict(file="og-health.png", icon="&#129658;", pill="Health Data",
         title="Philippine Health 1960&ndash;2024",
         sub="Sixty years of progress &mdash; and two indicators going the wrong way",
         stats=[("69.9 yrs", "Life Expectancy"), ("625", "TB per 100k"), ("World Bank", "Source")]),
    dict(file="og-ofw.png", icon="&#9992;&#65039;", pill="Migration",
         title="What Migration Sends Home",
         sub="$41.56B in 2025 &mdash; 5.33&times; all net foreign direct investment",
         stats=[("$41.56B", "Remittances 2025"), ("5.33&times;", "Net FDI"), ("World Bank", "Source")]),
    dict(file="og-poverty.png", icon="&#128176;", pill="Poverty &amp; Work",
         title="Poverty and the Jobs That Do Not Fix It",
         sub="2.24% unemployment, 33.6% vulnerable employment &mdash; work is not scarce, paid work is",
         stats=[("15.5%", "Below Poverty Line"), ("33.6%", "Vulnerable Work"), ("World Bank", "Source")]),
    dict(file="og-fies.png", icon="&#127968;", pill="Household Survey",
         title="What 41,544 Households Actually Spend",
         sub="The 2015 FIES microdata, opened &mdash; and Engel&rsquo;s law holding at every step",
         stats=[("41,544", "Households"), ("0.4438", "Gini"), ("FIES 2015", "Source")]),
]

if __name__ == "__main__":
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for s in SPECS:
        print("rendered", render(s, outdir))
