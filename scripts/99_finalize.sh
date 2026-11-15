#!/usr/bin/env bash
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
# Final clean run before submission (run from the repo root with the .venv active):
#   bash scripts/99_finalize.sh
# Records the environment, audits the 2 Sep optical coverage, regenerates web/docs/README from the tables,
# checks that withdrawn wording is gone, commits, pushes and waits for the GitHub Pages deploy of that commit.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/6 environment"
PYV=$(python --version 2>&1)
pip freeze --exclude-editable | grep -v "^-e " > requirements-lock.txt
sed -i "s|{{PYTHON_VERSION}}|${PYV}|" docs/reproduce.md
echo "     ${PYV}; $(wc -l < requirements-lock.txt) packages in requirements-lock.txt"

echo "== 2/6 audit of the 2 Sep optical coverage (per file, no mosaic)"
python scripts/02i_dswx_coverage_check.py | tee /tmp/coverage_check.txt
if grep -q "\[ALERT\]" /tmp/coverage_check.txt; then
  echo "STOP: the per-file check contradicts the mosaic; do not publish the coverage claim."; exit 2
fi

echo "== 3/6 regenerate wind check, web, documents and README from the tables"
python scripts/02e_dswx_compare.py > /dev/null
python scripts/02f_wind_check.py | tail -2
python scripts/03_export_web.py
python scripts/04_build_docs.py
python scripts/update_readme_results.py > /dev/null

echo "== 4/6 withdrawn wording must be gone from public texts"
if grep -niE "smoke|fire season|every 12 days|drop is real|ruled out|along shorelines|not imaged|not acquired|cloud-free|only Landsat|Evans et al\.? \(?2010|flooded forest|shallow,|shallow water|vegetated water declined|through cloud|\{\{PYTHON" \
     README.md web/index.html docs/demo/script.md docs/submission.md docs/reproduce.md docs/ai_use.md \
     outputs/tables/wind_check.csv; then
  echo "STOP: withdrawn wording found (lines above)."; exit 3
fi

echo "== 5/6 commit and push"
git add -A
git commit -m "Final clean run: environment lock, coverage audit, regenerated web, docs and README"
git push
SHA=$(git rev-parse HEAD)

echo "== 6/6 GitHub Pages deploy for ${SHA:0:7}"
RID=""
for i in $(seq 1 24); do
  RID=$(gh run list --workflow=pages.yml --commit "$SHA" --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
  [ -n "$RID" ] && break
  sleep 5
done
if [ -z "$RID" ]; then echo "No Pages run found for this commit (did web/ change?)."; exit 4; fi
gh run watch "$RID" --exit-status > /dev/null && echo "PAGES: success (run $RID)"
gh run list --workflow=pages.yml --limit 3
echo "FINAL COMMIT: $SHA"
