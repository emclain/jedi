#!/usr/bin/env bash
# agent-start.sh — Bootstrap a multi-agent session and claim one issue.
#
# Usage (from the primary checkout):
#   bash scripts/agent-start.sh                     # claim the top ready issue
#   bash scripts/agent-start.sh <issue-id>          # claim this issue
#   bash scripts/agent-start.sh --no-claim [<name>] # claim nothing
#
# The primary checkout is a coordination hub that no agent edits. This script
# fast-forwards it to origin/refactoring-test-coverage, makes sure the shared
# beads Dolt server is running, claims one issue, and creates an isolated
# worktree for it.
# With --no-claim it does all of that except the claim, for work that isn't a
# tracked issue; the worktree is named after <name> (default: a timestamp).
#
# On success, prints the worktree path and the claimed issue id.
# On "no work available", exits 0 with a message.
# On any hard error, exits non-zero.
#
# See MULTI_AGENT.md for the full procedure.

set -euo pipefail

usage() {
  sed -n 's/^#   //p' "$0" | sed 's/^/  /'
}

requested_id=""
no_claim=0
work_name=""
case "${1:-}" in
  "")
    ;;
  -h|--help)
    echo "Usage (from the primary checkout):"
    usage
    exit 0
    ;;
  --no-claim)
    no_claim=1
    work_name="${2:-session-$(date +%Y%m%d-%H%M%S)}"
    [ $# -le 2 ] || { echo "ERROR: too many arguments." >&2; usage >&2; exit 1; }
    ;;
  -*)
    echo "ERROR: unknown option '$1'." >&2
    usage >&2
    exit 1
    ;;
  *)
    requested_id="$1"
    [ $# -le 1 ] || { echo "ERROR: too many arguments." >&2; usage >&2; exit 1; }
    ;;
esac
# The name becomes a directory and a branch, so keep it to one plain segment.
if [ "$no_claim" -eq 1 ] && ! { [[ "$work_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] &&
    git check-ref-format "refs/heads/work/$work_name"; }; then
  echo "ERROR: --no-claim name '$work_name' must be letters, digits, '.', '_' or '-'." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

GIT_DIR_ABS="$(git rev-parse --path-format=absolute --git-dir)"
GIT_COMMON_ABS="$(git rev-parse --path-format=absolute --git-common-dir)"
if [ "$GIT_DIR_ABS" != "$GIT_COMMON_ABS" ]; then
  echo "ERROR: run agent-start.sh from the primary checkout, not a worktree." >&2
  echo "  cd $(dirname "$GIT_COMMON_ABS") && bash scripts/agent-start.sh" >&2
  exit 1
fi

# ── 1. Ensure required tools are on PATH ─────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"
# dolt is needed alongside bd: bd runs the shared `dolt sql-server` from it.
for tool in bd dolt jq python3; do
  if ! command -v "$tool" &>/dev/null; then
    echo "ERROR: $tool not found on PATH. See 'Beads Setup' and 'Setup' in AGENTS.md." >&2
    exit 1
  fi
done

# ── 2. Fast-forward the primary checkout ─────────────────────────────────────
# Worktrees branch from origin/refactoring-test-coverage directly; this keeps
# the hub's scripts and .beads config current, along with the code zuban's
# rename tests run against. It refuses rather than touch local work.
echo "Fast-forwarding primary checkout to origin/refactoring-test-coverage..."
git fetch origin refactoring-test-coverage
if [ "$(git branch --show-current)" != "refactoring-test-coverage" ]; then
  echo "ERROR: the primary checkout must stay on refactoring-test-coverage (it is on '$(git branch --show-current)')." >&2
  exit 1
fi
if ! git diff --quiet --ignore-submodules || ! git diff --cached --quiet --ignore-submodules; then
  echo "ERROR: the primary checkout has uncommitted changes. No agent should work in it;" >&2
  echo "move that work to a worktree, then re-run." >&2
  git status --short --untracked-files=no >&2
  exit 1
fi
if ! git merge --ff-only origin/refactoring-test-coverage; then
  echo "ERROR: the primary checkout could not fast-forward to origin/refactoring-test-coverage." >&2
  echo "If another agent was starting at the same moment, re-run. Otherwise it has local" >&2
  echo "commits or untracked files in the way; resolve that by hand." >&2
  exit 1
fi

# ── 3. Ensure submodules and the Python venv ─────────────────────────────────
# pip install -e needs the typeshed and django-stubs submodules present
# (setup.py asserts on both), and a fresh checkout doesn't have them yet.
echo "Ensuring submodules are present in the primary checkout..."
git submodule update --init

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python3 -c "import jedi" &>/dev/null 2>&1; then
  echo "Installing jedi in development mode..."
  pip install -q -e '.[testing]'
fi

# ── 4. Ensure the shared beads database is up ────────────────────────────────
# Parallel agents need beads' server mode: embedded mode is documented as
# single-writer. Every worktree resolves to this checkout's .beads/ through
# git's common dir, so they all talk to the one server this checkout runs.
if [ "$(jq -r .dolt_mode .beads/metadata.json)" != "server" ]; then
  echo "ERROR: .beads/metadata.json is not in server mode; parallel agents need the shared Dolt server." >&2
  echo "See 'Beads Database' in MULTI_AGENT.md." >&2
  exit 1
fi
fresh_db=0
[ -d .beads/dolt ] || fresh_db=1
bd dolt start
if [ "$fresh_db" -eq 1 ]; then
  # Fresh checkout: clone the database from the Dolt remote. Needs the server
  # up first, and unlike `bd init --force` it never deletes existing data.
  echo "No beads database yet — bootstrapping..."
  bd bootstrap --yes
fi

# ── 5. Claim one issue ───────────────────────────────────────────────────────
# `bd update --claim` is idempotent for the same actor, and bd's default actor
# is git user.name — shared by every agent in this environment. Without a
# unique actor, every agent would "win" the same issue. --no-claim sessions get
# one too, in case they claim something later.
export BEADS_ACTOR="agent-$(hostname)-$$"
claimed=""
if [ "$no_claim" -eq 1 ]; then
  echo "Not claiming an issue (--no-claim)."
elif [ -n "$requested_id" ]; then
  if ! issue_json="$(bd show "$requested_id" --json 2>/dev/null)"; then
    echo "ERROR: no issue matches '$requested_id'." >&2
    exit 1
  fi
  # bd resolves partial ids; the worktree and branch use the full one.
  requested_id="$(jq -r '.[0].id' <<<"$issue_json")"
  status="$(jq -r '.[0].status' <<<"$issue_json")"
  if [ "$status" = "closed" ]; then
    echo "ERROR: $requested_id is closed. Reopen it first if it needs more work:" >&2
    echo "  bd update $requested_id --status open" >&2
    exit 1
  fi
  if ! claim_err="$(bd update "$requested_id" --claim 2>&1 >/dev/null)"; then
    echo "ERROR: claiming $requested_id failed (status: $status," \
      "assignee: $(jq -r '.[0].assignee // "none"' <<<"$issue_json")): $claim_err" >&2
    exit 1
  fi
  claimed="$requested_id"
else
  ready_json="$(bd ready --json --limit 10)"
  for id in $(jq -r '.[].id' <<<"$ready_json"); do
    if claim_err="$(bd update "$id" --claim 2>&1 >/dev/null)"; then
      claimed="$id"
      break
    fi
    # Losing a claim race is expected; any other failure is not.
    if [ "$(bd show "$id" --json | jq -r '.[0].status')" = "in_progress" ]; then
      continue
    fi
    echo "ERROR: claiming $id failed: $claim_err" >&2
    exit 1
  done

  if [ -z "$claimed" ]; then
    echo "No available work — all issues are claimed or done."
    exit 0
  fi
fi

# ── 6. Create isolated worktree ──────────────────────────────────────────────
if [ -n "$claimed" ]; then
  echo "Claimed issue: $claimed"
  work_name="$claimed"
fi
worktree="../jedi-${work_name}"
worktree_abs="$(cd .. && pwd)/jedi-${work_name}"

if [ -d "$worktree" ] || git show-ref --verify --quiet "refs/heads/work/$work_name"; then
  if [ -z "$claimed" ]; then
    # Nothing marks an unclaimed worktree as abandoned, so never delete one.
    echo "ERROR: $worktree or branch work/$work_name already exists. Pick another name," >&2
    echo "or work in the existing worktree." >&2
    exit 1
  fi
  # A claimed issue's leftover worktree is from a prior crashed or blocked run.
  echo "Stale worktree found at $worktree — removing..."
  git worktree remove --force "$worktree" 2>/dev/null || true
  git branch -D "work/$claimed" 2>/dev/null || true
fi

git worktree add "$worktree" -b "work/$work_name" origin/refactoring-test-coverage

# Git worktrees do NOT inherit submodule contents — the directories exist but
# are empty. Initialize the typeshed submodule (required for tests) now so
# agents don't hit a confusing FileNotFoundError mid-run.
echo "Initializing submodules in worktree..."
git -C "$worktree" submodule update --init jedi/third_party/typeshed

echo "Worktree created at: $worktree_abs"

# ── 7. Write .agent-env ──────────────────────────────────────────────────────
# agent-land.sh lands work/$CLAIMED_ID and closes it, or work/$WORK_NAME when
# CLAIMED_ID is unset. Each form unsets the other variable, so one left in the
# shell by another worktree's .agent-env can't take over.
if [ -n "$claimed" ]; then
  id_lines="unset WORK_NAME
export CLAIMED_ID=$claimed"
else
  id_lines="unset CLAIMED_ID
export WORK_NAME=$work_name"
fi
cat > "$worktree/.agent-env" <<EOF
$id_lines
export BEADS_ACTOR="$BEADS_ACTOR"
EOF

echo ""
echo "Ready. Run the following to start work:"
echo "  cd $worktree_abs"
echo "  source $REPO_ROOT/.venv/bin/activate"
echo "  source .agent-env"
[ -z "$claimed" ] || echo "  bd show $claimed"
echo ""
echo "When done (work committed), land with:"
echo "  bash scripts/agent-land.sh"
