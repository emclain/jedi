#!/usr/bin/env bash
# agent-land.sh — Land one completed issue: quality gates, push, beads sync, cleanup.
#
# Usage (from the worktree, after committing your work):
#   bash scripts/agent-land.sh
#
# Reads CLAIMED_ID from the environment (source .agent-env first) or pass as $1.
# A worktree from `agent-start.sh --no-claim` sets WORK_NAME instead, and lands
# the same way except that there is no issue to close.
# Must be run from the worktree (not the primary checkout).

set -euo pipefail

# Guard: git refuses to operate in directories owned by a different user unless
# the path is explicitly listed in safe.directory.
_add_safe_dirs() {
  local dir
  for dir in "$@"; do
    git config --global --add safe.directory "$dir" 2>/dev/null || true
  done
}
if ! git rev-parse --git-common-dir &>/dev/null; then
  _add_safe_dirs "$(pwd)" "$(realpath "$(pwd)/..")"
  if ! git rev-parse --git-common-dir &>/dev/null; then
    echo "ERROR: git ownership check failed even after adding safe.directory." >&2
    exit 1
  fi
fi

claimed="${1:-${CLAIMED_ID:-}}"
work_name="${claimed:-${WORK_NAME:-}}"
if [ -z "$work_name" ]; then
  echo "ERROR: pass the issue id as \$1 or set CLAIMED_ID (source .agent-env)." >&2
  exit 1
fi
branch="work/$work_name"

git_common="$(git rev-parse --path-format=absolute --git-common-dir)"
if [ "$(git rev-parse --path-format=absolute --git-dir)" = "$git_common" ]; then
  echo "ERROR: run agent-land.sh from the issue's worktree, not the primary checkout." >&2
  exit 1
fi
MAIN_CHECKOUT="$(dirname "$git_common")"
WORKTREE_ROOT="$(git rev-parse --show-toplevel)"
cd "$WORKTREE_ROOT"
# The cleanup below removes this worktree, so it must be the one being landed.
if [ "$(git branch --show-current)" != "$branch" ]; then
  echo "ERROR: this worktree is on '$(git branch --show-current)', not $branch." >&2
  exit 1
fi

if ! git -C "$MAIN_CHECKOUT" rev-parse --git-dir &>/dev/null; then
  _add_safe_dirs "$MAIN_CHECKOUT"
fi

# Merge origin/refactoring-test-coverage into this branch. .beads/issues.jsonl
# is only an export of the shared beads database, so a conflict there is
# resolved by exporting again. A conflict in any other file stops the landing.
merge_origin() {
  git fetch origin refactoring-test-coverage
  if git merge origin/refactoring-test-coverage --no-edit; then
    return 0
  fi
  local conflicted
  conflicted="$(git diff --name-only --diff-filter=U)"
  if [ "$conflicted" = ".beads/issues.jsonl" ]; then
    echo "issues.jsonl conflict — re-exporting from the beads database..."
    bd export > .beads/issues.jsonl
    git add .beads/issues.jsonl
    git commit --no-edit
    return 0
  fi
  git merge --abort 2>/dev/null || true
  echo "ERROR: merging origin/refactoring-test-coverage failed. Conflicted files:" >&2
  echo "${conflicted:-(none — see git output above)}" >&2
  echo "Resolve it here (git merge origin/refactoring-test-coverage), commit, and re-run agent-land.sh." >&2
  exit 1
}

# Commit a fresh export of the shared database, if it differs from HEAD.
commit_export() {
  bd export > .beads/issues.jsonl
  git add .beads/issues.jsonl
  if ! git diff --cached --quiet -- .beads/issues.jsonl; then
    git commit -m "bd sync: update issues.jsonl after $work_name"
  fi
}

# Push $branch to refactoring-test-coverage. `git push` exits 1 both when
# another instance landed first and when the push can't happen at all (auth,
# network, a hook), so a failure is retried only if
# origin/refactoring-test-coverage has moved since we last saw it. Any
# arguments run as a command after each merge.
push_branch() {
  local attempt seen
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    seen="$(git rev-parse origin/refactoring-test-coverage)"
    if git push origin "$branch:refactoring-test-coverage"; then
      return 0
    fi
    git fetch origin refactoring-test-coverage
    if [ "$(git rev-parse origin/refactoring-test-coverage)" = "$seen" ]; then
      echo "ERROR: push failed" >&2
      exit 1
    fi
    echo "Push rejected — another instance landed first, retrying..."
    sleep 1
    merge_origin
    "$@"
  done
  echo "ERROR: push still rejected after $attempt attempts." >&2
  exit 1
}

# ── 1. Quality gates ─────────────────────────────────────────────────────────
echo "=== Quality gates ==="
# The venv lives in the primary checkout, with jedi installed there in editable
# mode. pytest imports this worktree's jedi because it runs from the worktree
# root; a plain script puts only its own directory on sys.path, so the smoke
# test needs PYTHONPATH or it would exercise the primary checkout's jedi.
# shellcheck disable=SC1091
source "$MAIN_CHECKOUT/.venv/bin/activate"
PYTHONPATH="$WORKTREE_ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 scripts/smoke_dependents.py
python3 -m pytest -v -k "refactor"

# ── 2. Push code to remote (retry loop handles concurrent instances) ─────────
# The issue stays in_progress until the code is on origin, so a landing that
# stops on a conflict never leaves a closed issue behind.
echo "=== Pushing code ==="
merge_origin
push_branch

# ── 3. Close the issue ───────────────────────────────────────────────────────
if [ -n "$claimed" ]; then
  echo "=== Closing $claimed ==="
  bd close "$claimed"
fi

# ── 4. Persist beads state ───────────────────────────────────────────────────
# Both are required (see "Beads Database" in MULTI_AGENT.md): the jsonl export
# for git, and bd dolt push for the Dolt history that `bd bootstrap` restores.
echo "=== Persisting beads state ==="
commit_export
push_branch commit_export

dolt_pushed=0
for attempt in 1 2 3; do
  if bd dolt push; then
    dolt_pushed=1
    break
  fi
  echo "bd dolt push failed (attempt $attempt/3)."
  sleep 2
done

# ── 5. Clean up worktree ─────────────────────────────────────────────────────
echo "=== Cleaning up ==="
cd "$MAIN_CHECKOUT"
git worktree remove --force "$WORKTREE_ROOT"  # --force needed: worktree contains submodule
git branch -d "$branch"

if [ "$dolt_pushed" -ne 1 ]; then
  echo "" >&2
  echo "ERROR: $work_name landed in git, but bd dolt push failed. Run it from $MAIN_CHECKOUT:" >&2
  echo "  bd dolt push" >&2
  exit 1
fi

echo ""
echo "✓ $work_name landed successfully."
