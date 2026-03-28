# Multi-Agent Workflow

Multiple Claude instances can work in parallel from the same checkout without conflicts by combining beads' atomic `--claim` with git worktrees.

## How It Works

- **Claim** serializes issue assignment — `bd update --claim` fails atomically if another instance beat you to it
- **Worktrees** give each instance its own working tree and index so file edits never interfere
- **The remote** is the only coordination point for git — instances never share a local branch

## Procedure

### 1. Startup (in the shared checkout)

```bash
cd /workspace/dev/jedi

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
git worktree add ../jedi-$claimed -b work/$claimed origin/refactoring-test-coverage
cd ../jedi-$claimed
```

Set a unique actor name so audit trails are distinguishable:

```bash
export BEADS_ACTOR="agent-$(hostname)-$$"
```

### 2. Work (in the worktree)

```bash
# Review the issue
bd show $claimed

# Do the work, then run quality gates
python3 -m pytest -v -k "refactor"

# Commit
git add <files>
git commit -m "<message>"
```

### 3. Landing the Plane (in the worktree)

```bash
# File issues for anything discovered but not completed
bd create --title="..." --type=task --priority=<n>

# Final quality gate
python3 -m pytest -v -k "refactor"

# Close the issue
bd close $claimed

# Push branch to remote (retry loop handles concurrent instances)
while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin work/$claimed:refactoring-test-coverage && break
  echo "Push rejected — another instance landed first, retrying..."
  sleep 1
done

# Persist beads state to git (bd dolt push is NOT used here — see note below)
bd export > .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "bd sync: update issues.jsonl after $claimed"

# Push beads state along with (or after) the code push — same retry loop applies
while true; do
  git fetch origin refactoring-test-coverage
  git merge origin/refactoring-test-coverage --no-edit
  git push origin work/$claimed:refactoring-test-coverage && break
  echo "Push rejected — another instance landed first, retrying..."
  sleep 1
done

# Clean up worktree
cd /workspace/dev/jedi
git worktree remove ../jedi-$claimed
git branch -d work/$claimed
```

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
