# Data pipeline. Scripts were previously run by hand from memory; this file is
# the record of what produces what, and it refuses to build a page from data
# that has not passed its checks.
#
# Setup once:   make venv
# Everything:   make check

PY      := .venv/bin/python
PROJECTS := $(sort $(dir $(wildcard data/*/checks.sql)))

.PHONY: help venv check facts lint clean-cache
help:
	@echo "make venv      create .venv and install the four tools"
	@echo "make check     run every project's checks.sql (non-zero exit on error)"
	@echo "make facts     verify every data-fact on every page resolves to a CSV row"
	@echo "make lint      static ReDoS scan over all build scripts"
	@echo "make rice      rebuild the rice panel, then check it"
	@echo "make pse       rebuild the PSE datasets, then check them"

venv:
	uv venv .venv
	uv pip install --python $(PY) duckdb pdfplumber tqdm regexploit

# --- validation -------------------------------------------------------------
check: facts backlinks sources
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
