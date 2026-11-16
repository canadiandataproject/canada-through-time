#!/usr/bin/env bash
# Publish site/ to GitHub Pages (the gh-pages branch). Build first: python tools/build_site.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; TMP="$(mktemp -d)"
git clone -q --depth 1 -b gh-pages "$(git -C "$ROOT" remote get-url origin)" "$TMP"
find "$TMP" -mindepth 1 -maxdepth 1 ! -name .git ! -name media -exec rm -rf {} +   # media/ hosts videos for scheduled posts: never wipe it
cp -r "$ROOT/site/." "$TMP/"
cd "$TMP" && git add -A && git -c user.name="The Canadian Data Project" -c user.email="357254700+canadiandataproject@users.noreply.github.com" commit -qm "Publish site (built from $(git -C "$ROOT" rev-parse --short HEAD))" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"$'\n'"Claude-Session: https://claude.ai/code/session_011gAejeoNAPcWy2aNt47H5Z" && git push -q origin gh-pages
echo "published; GitHub Pages updates in about a minute"
