# Multi-Agent Workflow

Multiple Claude instances can work in parallel from the same checkout without conflicts by combining beads' atomic `--claim` with git worktrees.

## How It Works

- **Claim** serializes issue assignment — `bd update --claim` fails atomically if another instance beat you to it
- **Worktrees** give each instance its own working tree and index so file edits never interfere
- **The remote** is the only coordination point for git — instances never share a local branch

## One Issue Per Session

Each agent instance should claim and complete **exactly one issue**, then stop. Do not loop back to claim another. This keeps each agent's scope small and avoids long-running sessions that accumulate stale state or conflict with other instances.

## Procedure

### 1. Startup (in the shared checkout)

The preferred path is the startup script, which handles all guard conditions automatically:

```bash
cd /workspace/dev/jedi
bash scripts/agent-start.sh
```

If the script prints a worktree path, `cd` there and continue. If it prints "No available work", stop.

Manual equivalent (for reference or debugging):

```bash
cd /workspace/dev/jedi

# Ensure bd is initialized
if ! bd list &>/dev/null; then
  bd init --force --prefix jedi
  bd import
fi

# Ensure venv exists and is activated
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -e '.[testing]'

# Pull latest
git pull origin refactoring-test-coverage

# Find and claim the highest-priority available issue
claimed=""
for id in $(bd ready --json --limit 10 | jq -r '.[].id'); do
  if bd update "$id" --claim 2>/dev/null; then
    claimed="$id"
    break
  fi
done

[ -z "$claimed" ] && echo "No available work." && exit 0

# Create an isolated worktree + branch for this issue
# If a stale worktree exists from a crashed prior run, remove it first
if [ -d "../jedi-$claimed" ]; then
  git worktree remove --force "../jedi-$claimed" 2>/dev/null || true
  git branch -D "work/$claimed" 2>/dev/null || true
fi
git worktree add ../jedi-$claimed -b work/$claimed origin/refactoring-test-coverage

# Worktrees do NOT inherit submodule contents — initialize typeshed or tests fail
git -C ../jedi-$claimed submodule update --init jedi/third_party/typeshed

# Worktrees also do NOT inherit .beads/ — bd would start a fresh Dolt server
# with an empty database.  Copy the config and port file so bd in the worktree
# connects to the same already-running server as the main checkout.
mkdir -p ../jedi-$claimed/.beads
cp .beads/config.yaml ../jedi-$claimed/.beads/
[ -f .beads/dolt-server.port ] && cp .beads/dolt-server.port ../jedi-$claimed/.beads/

# Write .agent-env so the agent can source it instead of typing exports
cat > ../jedi-$claimed/.agent-env <<EOF
export CLAIMED_ID=$claimed
export BEADS_ACTOR="agent-$(hostname)-$$"
EOF

cd ../jedi-$claimed
```

Set a unique actor name so audit trails are distinguishable — `agent-start.sh` writes
`.agent-env` into the worktree for this:

```bash
source .agent-env   # sets CLAIMED_ID and BEADS_ACTOR
```

### 2. Work (in the worktree)

```bash
# Review the issue
bd show $CLAIMED_ID

# Do the work, then run quality gates
python3 -m pytest -v -k "refactor"

# Commit
git add <files>
git commit -m "<message>"
```

### 3. Landing the Plane (in the worktree)

First, file any follow-up issues for work you discovered but didn't complete:

```bash
bd create --title="..." --type=task --priority=<n>
```

Then run the landing script, which handles quality gates, `bd close`, both push retry
loops, beads-state persistence, and worktree cleanup automatically:

```bash
bash scripts/agent-land.sh
```

`bd` commands work in the worktree because `agent-start.sh` copied `.beads/config.yaml`
and `.beads/dolt-server.port` there so bd connects to the same Dolt server as the main
checkout.  If the Dolt server restarted (stale port), `agent-land.sh` detects the failure,
refreshes the port file from the main checkout, and retries automatically.

<details>
<summary>Manual equivalent (for reference or debugging)</summary>

```bash
python3 scripts/smoke_dependents.py
python3 -m pytest -v -k "refactor"

bd close $CLAIMED_ID

while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin "work/$CLAIMED_ID:refactoring-test-coverage" && break
  echo "Push rejected — another instance landed first, retrying..."
  sleep 1
done

bd export > .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "bd sync: update issues.jsonl after $CLAIMED_ID"

while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin "work/$CLAIMED_ID:refactoring-test-coverage" && break
  echo "Push rejected — retrying..."
  sleep 1
done

cd /workspace/dev/jedi
git worktree remove --force "../jedi-$CLAIMED_ID"
git branch -d "work/$CLAIMED_ID"
```
</details>

### 4. **MANDATORY: Reflect on Workflow** (do this even if everything went smoothly)

Before stopping, explicitly confirm or improve the workflow experience:

- **If workflow was smooth:** write one sentence saying so (e.g., "Workflow was clean — no issues").
- **If `scripts/agent-start.sh` or `agent-land.sh` failed or was incomplete:** improve it.
- **If setup instructions in AGENTS.md were wrong or missing a step:** update them.
- **If a new category of obstacle appeared:** add it to the script's guard logic.
- **If any step is currently prose instructions:** convert it to scripted commands in `agent-*.sh` — scripts are more reliable than prose and should be preferred wherever possible.

The goal: the next agent should be able to run `bash scripts/agent-start.sh` and end up in a worktree ready to work with no manual intervention; then do their work and run `bash scripts/agent-land.sh` to successfully "land the plane" and push work back to origin.

**Stop after one issue.** Do not loop back to claim another.

## Beads State Persistence

`bd dolt push` is **not configured** in this environment — there is no dolt remote. Running it will always fail with `remote 'origin' not found`.

Beads state is instead persisted through the git-tracked `.beads/issues.jsonl` file. This is the canonical source for future sessions: `bd init` + `bd import` on a fresh checkout reads from it.

**To persist issue changes (closes, updates, new issues) for future sessions:**

```bash
bd export > .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "bd sync: ..."
git push origin <branch>:refactoring-test-coverage
```

If `issues.jsonl` is not updated and pushed, any issue state changes made during the session (closures, claims, new issues) will be **invisible to future sessions** that re-run `bd import` from git. The local dolt database under `.beads/dolt/` is runtime state and is not preserved across containers or fresh checkouts.

## Why This Is Safe

- **No local `refactoring-test-coverage` branch is ever modified.** The shared checkout stays on its branch untouched. Instances push `work/$claimed:refactoring-test-coverage` directly to the remote, so there is no shared local state to corrupt.
- **Push rejection is the coordination signal.** If two instances finish at the same time, one push is rejected. The loser fetches, merges into its worktree, and retries — entirely in isolation.
- **`--claim` is atomic.** Two instances seeing the same issue in `bd ready` output will race to claim it; exactly one succeeds. The loser moves to the next candidate.
