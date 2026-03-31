# Multi-Agent Workflow

Multiple Claude instances can work in parallel from the same checkout without conflicts by combining beads' atomic `--claim` with git worktrees. Each instance claims one issue, works in an isolated worktree, and pushes via `work/<id>:refactoring-test-coverage` — the remote is the only coordination point.

## One Issue Per Session

Each agent instance should claim and complete **exactly one issue**, then stop.

## Procedure

### 1. Startup

```bash
cd /workspace/dev/jedi
bash scripts/agent-start.sh
```

If the script prints a worktree path, `cd` there and continue. If it prints "No available work", stop.

### 2. Work (in the worktree)

```bash
source .agent-env   # sets CLAIMED_ID and BEADS_ACTOR

bd show $CLAIMED_ID

# Do the work, then run quality gates
python3 -m pytest -v -k "refactor"

git add <files>
git commit -m "<message>"
```

### 3. Landing the Plane (in the worktree)

File any follow-up issues first:

```bash
bd create --title="..." --type=task --priority=<n>
```

Then land:

```bash
bash scripts/agent-land.sh
```

The script runs quality gates, closes the issue, persists beads state, pushes (with retry on rejection), and removes the worktree.

### 4. **MANDATORY: Reflect on Workflow**

- **If workflow was smooth:** write one sentence saying so.
- **If `agent-start.sh` or `agent-land.sh` failed or was incomplete:** improve it.
- **If setup instructions in AGENTS.md were wrong or missing a step:** update them.
- **If any step is currently prose instructions:** convert it to scripted commands.

The goal: the next agent should be able to run `bash scripts/agent-start.sh`, do their work, and run `bash scripts/agent-land.sh` with no manual intervention.

**Stop after one issue.**

## Beads State Persistence

`bd dolt push` is not configured — there is no dolt remote. Beads state is persisted via `.beads/issues.jsonl` in git. `agent-land.sh` handles this automatically; on a fresh checkout, `bd init --force --prefix jedi && bd import` restores state from that file.
