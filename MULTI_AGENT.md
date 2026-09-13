# Multi-Agent Workflow

Multiple Claude instances can work in parallel from the same checkout without conflicts by combining beads' atomic `--claim` with git worktrees. Each instance claims one issue, works in an isolated worktree, and pushes via `work/<id>:refactoring-test-coverage` — the remote is the only coordination point.

## One Issue Per Session

Each agent instance should claim and complete **exactly one issue**, then stop.

Work only what the issue describes. If you notice related problems, edge cases, or tempting tangents, file a bead and move on — do not investigate or fix them. Staying narrowly focused keeps sessions short and avoids conflicts with other instances.

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

File beads for anything you noticed but didn't work on — related issues, edge cases, tangents. Do not pursue them.

```bash
bd create --title="..." --type=task --priority=<n>
```

Then land:

```bash
bash scripts/agent-land.sh
```

The script runs quality gates, closes the issue, persists beads state, pushes (with retry on rejection), and removes the worktree.

### 4. **MANDATORY: Reflect on Workflow**

Before stopping, review the session for friction, gaps, or follow-up work. This step is **not optional** — do not skip it.

**For every issue you encountered or discovered (permission errors, missing steps, unclear instructions, new edge cases):**

Fix in-place (only when the fix is clear and unambiguous):
- **If `scripts/agent-start.sh` or `agent-land.sh` failed or was incomplete:** improve the script.
- **If setup instructions in AGENTS.md were wrong or missing a step:** update them.
- **If a new category of obstacle appeared:** add it to the script's guard logic.
- **If any step is currently prose instructions:** convert it to scripted commands.

File a bead for anything requiring deeper investigation or design:
1. **File a bead** — `bd create --title="..." --description="..." --type=task --priority=<n>`
2. **Push any new beads** — run `bd export > .beads/issues.jsonl`, commit, and push to `refactoring-test-coverage`.

**If workflow was smooth with no issues:** write one sentence saying so — no bead needed.

The goal: the next agent should be able to run `bash scripts/agent-start.sh`, do their work, and run `bash scripts/agent-land.sh` with no manual intervention.

**Stop after one issue.**

## Beads State Persistence

This repo has a real Dolt remote (`sync.remote` in `.beads/config.yaml`, schema migrated to v53 on 2026-09-13). `bd dolt push` works and should be used alongside `.beads/issues.jsonl` in git, not instead of it. `agent-land.sh` handles the export automatically; on a fresh checkout, `bd bootstrap` clones the Dolt database from the remote (do not use `bd init --force` — it refuses once a remote has history).
