#!/usr/bin/env bash
# agent-start.sh — Bootstrap a multi-agent session and claim one issue.
#
# Usage:
#   cd /workspace/dev/jedi
#   bash scripts/agent-start.sh
#
# On success, prints the worktree path and the claimed issue id.
# On "no work available", exits 0 with a message.
# On any hard error, exits non-zero.
#
# The agent should then:
#   cd <worktree path>
#   export BEADS_ACTOR="agent-$(hostname)-$$"
#   bd show $CLAIMED_ID   # and proceed from there
#
# See MULTI_AGENT.md for the full procedure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ── 1. Ensure bd is on PATH ───────────────────────────────────────────────────
if ! command -v bd &>/dev/null; then
  echo "bd not found — installing..."
  if curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash; then
    echo "bd installed via install script."
  else
    echo "Install script failed, trying direct dolt binary download..."
    ARCH=$(uname -m)
    [ "$ARCH" = "aarch64" ] && ARCH="arm64"
    curl -fsSL "https://github.com/dolthub/dolt/releases/latest/download/dolt-linux-${ARCH}.tar.gz" \
      | tar -xz -C /tmp
    mkdir -p "$HOME/.local/bin"
    cp "/tmp/dolt-linux-${ARCH}/bin/dolt" "$HOME/.local/bin/bd"
    chmod +x "$HOME/.local/bin/bd"
    export PATH="$HOME/.local/bin:$PATH"
    echo "bd installed to ~/.local/bin/bd"
  fi
fi

# PATH may need updating if bd was just installed
export PATH="$HOME/.local/bin:$PATH"

if ! command -v bd &>/dev/null; then
  echo "ERROR: bd still not found after installation attempt. Add ~/.local/bin to PATH." >&2
  exit 1
fi

# ── 2. Ensure jq is available (needed for --json parsing) ────────────────────
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is not installed. Install it with: apt-get install -y jq" >&2
  exit 1
fi

# ── 3. Initialize beads if not already done ──────────────────────────────────
if ! bd list &>/dev/null 2>&1; then
  echo "Initializing beads database..."
  bd init --force --prefix jedi
  bd import
fi

# ── 4. Ensure Python venv exists and dependencies are installed ──────────────
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

# ── 5. Pull latest ────────────────────────────────────────────────────────────
echo "Pulling latest from origin/refactoring-test-coverage..."
git pull origin refactoring-test-coverage

# ── 6. Claim one issue ───────────────────────────────────────────────────────
claimed=""
for id in $(bd ready --json --limit 10 | jq -r '.[].id'); do
  if bd update "$id" --claim 2>/dev/null; then
    claimed="$id"
    break
  fi
done

if [ -z "$claimed" ]; then
  echo "No available work — all issues are claimed or done."
  exit 0
fi

echo "Claimed issue: $claimed"

# ── 7. Create isolated worktree ──────────────────────────────────────────────
worktree="../jedi-${claimed}"
worktree_abs="$(cd .. && pwd)/jedi-${claimed}"

# Clean up stale worktree from a prior crashed run
if [ -d "$worktree" ]; then
  echo "Stale worktree found at $worktree — removing..."
  git worktree remove --force "$worktree" 2>/dev/null || true
  git branch -D "work/$claimed" 2>/dev/null || true
fi

git worktree add "$worktree" -b "work/$claimed" origin/refactoring-test-coverage

# Git worktrees do NOT inherit submodule contents — the directories exist but
# are empty. Initialize the typeshed submodule (required for tests) now so
# agents don't hit a confusing FileNotFoundError mid-run.
echo "Initializing submodules in worktree..."
git -C "$worktree" submodule update --init jedi/third_party/typeshed

# Git worktrees also do NOT inherit .beads/ — bd would spin up a fresh Dolt
# server with an empty database and fail with "database not found".
# Copy the config and the running server's port file so bd in the worktree
# connects to the same server (and same beads_jedi database) as this checkout.
echo "Bridging bd into worktree..."
mkdir -p "$worktree/.beads"
cp "$REPO_ROOT/.beads/config.yaml" "$worktree/.beads/"
if [ -f "$REPO_ROOT/.beads/dolt-server.port" ]; then
  cp "$REPO_ROOT/.beads/dolt-server.port" "$worktree/.beads/"
fi

echo "Worktree created at: $worktree_abs"

# ── 8. Write .agent-env so the agent can source it instead of typing exports ─
cat > "$worktree/.agent-env" <<EOF
export CLAIMED_ID=$claimed
export BEADS_ACTOR="agent-$(hostname)-$$"
EOF

echo ""
echo "Ready. Run the following to start work:"
echo "  cd $worktree_abs"
echo "  source $REPO_ROOT/.venv/bin/activate"
echo "  source .agent-env"
echo "  bd show $claimed"
echo ""
echo "When done (work committed), land with:"
echo "  bash scripts/agent-land.sh"
