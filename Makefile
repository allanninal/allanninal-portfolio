# Data pipeline. Scripts were previously run by hand from memory; this file is
# the record of what produces what, and it refuses to build a page from data
# that has not passed its checks.
#
# Setup once:   make venv
# Everything:   make check

PY      := .venv/bin/python
PROJECTS := $(sort $(dir $(wildcard data/*/checks.sql)))

.PHONY: help venv check facts lint scripts render sitemap tracked clean-cache
help:
	@echo "make venv      create .venv and install the four tools"
	@echo "make check     run every project's checks.sql (non-zero exit on error)"
	@echo "make facts     verify every data-fact on every page resolves to a CSV row"
	@echo "make lint      static ReDoS scan over all build scripts"
	@echo "make render    load every page in headless Chromium and check it paints (needs a server on :8971)"
	@echo "make sitemap   verify sitemap-pages.xml is current and every sitemap covers its pages"
	@echo "make tracked   verify every /build series part is committed, not just generated"
	@echo "make rice      rebuild the rice panel, then check it"
	@echo "make pse       rebuild the PSE datasets, then check them"

venv:
	uv venv .venv
	uv pip install --python $(PY) duckdb pdfplumber tqdm regexploit

# --- validation -------------------------------------------------------------
check: facts backlinks sources reveal styling scripts sitemap tracked
	@$(PY) data/_lib/check.py

# Prose numbers are typed by hand while reading a CSV -- the same process that
# put a sign error and a phantom all-time high on the PSE page. This makes a
# figure that does not round-trip to a row impossible to publish.
facts:
	@$(PY) tools/verify_facts.py

lint:
	@.venv/bin/regexploit-py $$(find data tools -name '*.py') || true

# --- rice -------------------------------------------------------------------
RICE     := data/ph-food-prices/ph_rice_prices_daily.csv
RICE_COV := data/ph-food-prices/ph_rice_prices_coverage.csv

$(RICE) $(RICE_COV): data/ph-food-prices/_build/fetch_bantay_presyo.py
	$(PY) $<

data/ph-food-prices/ph_rice_annual.csv: $(RICE) data/ph-food-prices/_build/build_series.py
	$(PY) data/_lib/check.py data/ph-food-prices
	$(PY) data/ph-food-prices/_build/build_series.py

rice: data/ph-food-prices/ph_rice_annual.csv

# --- PSE --------------------------------------------------------------------
PSE := data/ph-pse/ph_psei_annual.csv

$(PSE): data/ph-pse/_build/fetch_pse.py
	$(PY) $<

pse: $(PSE)
	$(PY) data/_lib/check.py data/ph-pse

clean-cache:
	find data -name '.cache' -type d -prune -exec rm -rf {} +

# A project page quotes its blog post's title in the back-link box. Retitling
# the post leaves that quote stale, below the fold, in prose -- four pages were
# wrong before this ran in CI.
backlinks:
	@$(PY) tools/nav/sync_backlinks.py --check

# Citations are declared once per project in data/<project>/sources.csv and
# rendered onto the page from there. The electricity page's footer once credited
# the World Food Programme and the DOH because it had been copied from another
# page, and twenty of twenty-seven pages had no citation line at all.
sources:
	@$(PY) tools/pages/sources.py --check

# Two pages shipped with .fade-up { opacity: 0 } and nothing that ever added the
# .visible class, so parts of them were invisible from publication. Every other
# check passed the whole time: the markup was there, the facts verified, the tags
# balanced. Nothing tested what a browser paints.
reveal:
	@$(PY) tools/pages/reveal.py --check

# A class the page's own stylesheet never defines is still valid markup, so it
# passes every other check and renders as unstyled stacked text. Two pages
# shipped that way after being regenerated with the wrong class vocabulary.
styling:
	@$(PY) tools/pages/styling.py

# sitemap-pages.xml was hand-maintained and had drifted twice: eight pages
# missing entirely (including electricity and rice-prices), and every lastmod
# reading late August while the pages had been rewritten that day. Neither is
# visible by looking at the file -- it is well-formed XML with plausible dates.
# Generated from the filesystem now, with lastmod from the last commit that
# touched each page rather than from mtime.
sitemap:
	@$(PY) tools/nav/sitemap.py --check
	@$(PY) tools/nav/sitemap.py --audit

# .gitignore had `!/build/` on line 3 saying /build is published site content, and
# a bare `build/` on line 60. Last match wins, so every NEW file under build/ was
# silently dropped from `git add -A` -- the 1,067 older ones stayed tracked, which
# is why 133 days were fine and the 134th shipped with its landing card live and
# all seven articles 404. Compares the registry against git ls-files, not the
# filesystem, because the files existed locally the whole time.
tracked:
	@$(PY) tools/awsbuild/tracked.py --check

# Nothing static can tell you whether a page paints. Two pages shipped visibly
# broken while every check below passed. This loads each one in headless Chromium,
# scrolls to fire the reveal observers, then fails on a canvas with no pixels, a
# .fade-up still transparent, a horizontal page scroll, or a same-origin console
# error. Needs a server: python3 -m http.server 8971
render:
	@node tools/pages/render_check.js $$(ls projects/*.html blog/*.html | sed 's|^|http://localhost:8971/|')

# An older nav injector left <script defer src="/assets/site-nav.js"> open in the
# middle of the dengue page's chart block. A src script ignores its inline
# content, so two chart configs never ran and two canvases were blank from
# publication -- past valid JS, verified facts, balanced tags and parsing
# JSON-LD. Only a browser could see it, and nothing was looking.
scripts:
	@$(PY) tools/pages/scripts.py
