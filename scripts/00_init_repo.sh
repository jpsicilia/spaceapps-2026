#!/usr/bin/env bash
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
# Step 1a: create the public GitHub repo from the prepared skeleton.
# Run from the repo root:  bash scripts/00_init_repo.sh
set -euo pipefail

REPO_NAME="${1:-spaceapps-2026}"
DESC="Pantanal 2026: the water that left, seen by NISAR radar (NASA Space Apps 2026 - Dancing with the SARs)"

cd "$(dirname "$0")/.."

# 1) data/ must never be committed
touch .gitignore
for pat in "data/" ".venv/" "__pycache__/" "*.h5" "_practica/"; do
  grep -qxF "$pat" .gitignore || echo "$pat" >> .gitignore
done

# 2) git init (only if needed)
[ -d .git ] || git init -b main
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "Initial skeleton + GCOV preprocessing (step 1)"
fi

# 3) safety check: nothing heavy staged
BIG=$(git ls-files | xargs -r du -k 2>/dev/null | awk '$1 > 50000 {print $2}')
if [ -n "$BIG" ]; then
  echo "[ERROR] Files > 50 MB are tracked, fix before pushing:"; echo "$BIG"; exit 1
fi

# 4) create public repo and push
if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  gh repo create "$REPO_NAME" --public --description "$DESC" --source=. --remote=origin --push
fi
gh repo view --web >/dev/null 2>&1 || true
echo "Repo: $(git remote get-url origin)"
