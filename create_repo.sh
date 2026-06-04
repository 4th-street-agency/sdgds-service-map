#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-sdgds-service-map}"
command -v gh >/dev/null || { echo "GitHub CLI (gh) not found. Install: https://cli.github.com"; exit 1; }
git init -q
git add -A
git commit -qm "SDGDS service-area map" || true
gh repo create "$REPO" --public --source=. --remote=origin --push
USER=$(gh api user -q .login)
# enable GitHub Pages on main / root
gh api -X POST "repos/$USER/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
  || gh api -X PUT "repos/$USER/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 || true
echo ""
echo "Repo:      https://github.com/$USER/$REPO"
echo "Embed URL: https://$USER.github.io/$REPO/   (live in ~1 min)"
