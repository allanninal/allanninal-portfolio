#!/usr/bin/env bash
# Build a field-notes section and everything downstream of it, in the one order
# that works.
#
#   ./tools/fieldnotes/ship.sh stripe 2026-08-30
#
# The order is not arbitrary and the failures it prevents are silent:
#   - build.py rewrites every page in the section from scratch, destroying the
#     repo CTA that add_repo_links.py injects. So the CTA is re-injected after.
#   - build_fix_repos.py parses the BUILT HTML, so it has to follow the build.
#   - add_repo_links.py prints the field guide's file size, so the PDF has to be
#     rebuilt before it, or the page advertises the previous size.
set -euo pipefail
cd "$(dirname "$0")/../.."

sec="${1:?usage: ship.sh <section> <YYYY-MM-DD>}"
date="${2:?usage: ship.sh <section> <YYYY-MM-DD>}"

echo "== $sec: photos"
python3 tools/fieldnotes/pick_images.py "$sec" --apply | tail -2
echo "== $sec: checks"
python3 tools/fieldnotes/check_section.py "$sec" --run-tests
echo "== $sec: build"
( cd "tools/fieldnotes/$sec" && python3 build.py | tail -1 )
echo "== $sec: sitemap"
python3 tools/fieldnotes/make_sitemap.py "$sec" --date "$date" --apply | head -1
echo "== $sec: repo"
python3 tools/fieldnotes/build_fix_repos.py --apply --publish "$sec" | grep "$sec"
echo "== $sec: field guide"
python3 tools/fieldnotes/build_field_guides.py --apply "$sec" | tail -1
echo "== $sec: repo links"
python3 tools/fieldnotes/add_repo_links.py --apply "$sec" | tail -2
echo "== $sec: read-only audit of the published repo"
python3 tools/fieldnotes/audit_readonly.py
echo "== site: nav + homepage"
python3 tools/nav/apply.py | tail -1
./tools/nav/deploy_home.sh | tail -1
