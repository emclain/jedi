#!/usr/bin/env bash
# agent-land.sh — Land one completed issue: quality gates, push, beads sync, cleanup.
#
# Usage (from the worktree, after committing your work):
#   bash scripts/agent-land.sh
#
# Reads CLAIMED_ID from the environment (source .agent-env first) or pass as $1.
# Must be run from the worktree (not the main checkout).

set -euo pipefail

claimed="${1:-${CLAIMED_ID:-}}"
if [ -z "$claimed" ]; then
  echo "ERROR: pass the issue id as \$1 or set CLAIMED_ID (source .agent-env)." >&2
  exit 1
fi

# Find the main checkout via git's common dir (works from both worktree and main checkout)
git_common="$(git rev-parse --git-common-dir)"
if [[ "$git_common" = /* ]]; then
  # In a worktree: git-common-dir is an absolute path inside the main checkout's .git
  MAIN_CHECKOUT="$(dirname "$git_common")"
else
  MAIN_CHECKOUT="$(git rev-parse --show-toplevel)"
fi
WORKTREE_ROOT="$(git rev-parse --show-toplevel)"

# Helper: run a bd command; if it fails, refresh the server port file and retry once.
# This handles the case where the Dolt server restarted and the port changed.
bd_run() {
  if ! bd "$@" 2>/dev/null; then
    echo "bd $* failed — refreshing server port from main checkout and retrying..."
    if [ -f "$MAIN_CHECKOUT/.beads/dolt-server.port" ]; then
      cp "$MAIN_CHECKOUT/.beads/dolt-server.port" "$WORKTREE_ROOT/.beads/dolt-server.port"
    fi
    bd "$@"
  fi
}

# ── 1. Quality gates ─────────────────────────────────────────────────────────
echo "=== Quality gates ==="
python3 "$WORKTREE_ROOT/scripts/smoke_dependents.py"
python3 -m pytest -v -k "refactor"

# ── 2. Close the issue ───────────────────────────────────────────────────────
echo "=== Closing $claimed ==="
bd_run close "$claimed"

# ── 3. Push code to remote (retry loop handles concurrent instances) ─────────
echo "=== Pushing code ==="
while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin "work/$claimed:refactoring-test-coverage" && break
  echo "Push rejected — another instance landed first, retrying..."
  sleep 1
done

# ── 4. Persist beads state ───────────────────────────────────────────────────
echo "=== Persisting beads state ==="
bd_run export > "$WORKTREE_ROOT/.beads/issues.jsonl"
git add .beads/issues.jsonl
git commit -m "bd sync: update issues.jsonl after $claimed"

while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin "work/$claimed:refactoring-test-coverage" && break
  echo "Push rejected — retrying..."
  sleep 1
done

# ── 5. Clean up worktree ─────────────────────────────────────────────────────
echo "=== Cleaning up ==="
cd "$MAIN_CHECKOUT"
git worktree remove --force "$WORKTREE_ROOT"  # --force needed: worktree contains submodule
git branch -d "work/$claimed"

echo ""
echo "✓ $claimed landed successfully."
