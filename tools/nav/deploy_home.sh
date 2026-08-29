#!/usr/bin/env bash
# Build the homepage and publish it to the repo root, which is what GitHub
# Pages serves.
#
# Only index.html, 404.html and _astro/ move. The rest of dist/ (sitemap-0.xml,
# ads.txt, og-image.*) is either generated differently at the root or already
# maintained there by hand, and copying it would overwrite the real files.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"

# site-nav.js is served from /assets on the deployed site; the copy under
# redesign/public exists so `astro dev` and `astro preview` resolve it too.
mkdir -p redesign/public/assets
cp assets/site-nav.js redesign/public/assets/site-nav.js

cd redesign
npx astro build

cd "$ROOT"
rm -rf _astro
cp -R redesign/dist/_astro _astro
cp redesign/dist/index.html index.html
cp redesign/dist/404.html 404.html
echo "published: index.html, 404.html, _astro/"
