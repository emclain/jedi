# Multi-Agent Workflow

Multiple Claude instances can work in parallel in one environment by combining beads' atomic `--claim`, a shared beads Dolt server, and one git worktree per issue.

## How It Works

- **Claim** serializes issue assignment — `bd update --claim` fails atomically if another instance beat you to it. Each instance claims under its own `BEADS_ACTOR`; a claim is idempotent for the same actor, so a shared actor would let every instance "win" the same issue.
- **The beads server** is the one database every instance writes to. Beads' embedded mode is single-writer, so parallel agents require server mode (see [Beads Database](#beads-database)).
- **Worktrees** give each instance its own working tree and index, so file edits never interfere.
- **The remote** is the only coordination point for git — instances push `work/<id>:refactoring-test-coverage` and never share a local branch.

## The Primary Checkout

The primary checkout (the directory holding `.git/`, e.g. `dev/jedi`) is a coordination hub. **No agent edits files in it or commits from it** — including agents working on other repositories (running `bd` there is fine; it only touches the database). It holds shared state:

- **The beads database and server.** Every worktree resolves `.beads/` to the primary's through git's common directory, so all `bd` commands reach the server running from the primary's `.beads/dolt/` (PID, port and log files sit beside it; all gitignored).
- **Its own `refactoring-test-coverage` branch and working tree.** `agent-start.sh` fast-forwards them to `origin/refactoring-test-coverage`, which is how script and `.beads` config changes pushed by other agents reach the hub. It refuses to run if the primary has uncommitted changes or local commits.
- **Submodules and the Python venv.** `agent-start.sh` initializes `jedi/third_party/typeshed` and `django-stubs` here and creates `.venv` with jedi installed in editable mode. Worktrees use this venv; running from a worktree's root still imports the worktree's own `jedi/` (see [Work](#2-work-in-the-worktree)).
- **Worktree bookkeeping.** Creating and removing worktrees and `work/<id>` branches changes `.git/`; the worktrees themselves live beside it as `../jedi-<id>`.

**zuban reads this checkout.** zuban's `scripts/run_jedi_rename_tests.sh` runs `test/test_lsp_rename.py` (with `test/lsp_compat.py`) from here. zuban agents treat it as read-only: a change zuban needs in jedi is filed as a bead in this repository and worked like any other issue. Because `agent-start.sh` fast-forwards this checkout, a zuban test run can see these files change mid-run.

## One Issue Per Session

Each agent instance should claim and complete **exactly one issue**, then stop.

Work only what the issue describes. If you notice related problems, edge cases, or tempting tangents, file a bead and move on — do not investigate or fix them. Staying narrowly focused keeps sessions short and avoids conflicts with other instances.

## Procedure

The scripts are the procedure; read them rather than a copy here, which would drift.

### 1. Startup (in the primary checkout)

```bash
bash scripts/agent-start.sh
```

If the script prints a worktree path, `cd` there and continue. If it prints "No available work", stop. If it fails because another instance was starting at the same moment (a git lock error), run it again.

To claim a specific issue rather than the top ready one, pass its id: `bash scripts/agent-start.sh <id>`. For work that is not a tracked issue, such as a change a user asks for directly, `bash scripts/agent-start.sh --no-claim [<name>]` does everything except the claim, in `../jedi-<name>` on `work/<name>`; `agent-land.sh` lands that worktree the same way, minus closing an issue.

What it does: checks for `bd`, `dolt`, `jq` and `python3`; fast-forwards the primary checkout; initializes its submodules and venv; starts the beads server (`bd dolt start`, bootstrapping the database on a fresh checkout); claims the highest-priority ready issue under a unique `BEADS_ACTOR`; creates `../jedi-<id>` on branch `work/<id>` from `origin/refactoring-test-coverage` with the typeshed submodule initialized; and writes `.agent-env` into it.

### 2. Work (in the worktree)

```bash
cd ../jedi-<id>
source ../jedi/.venv/bin/activate   # the primary checkout's venv
source .agent-env                   # sets CLAIMED_ID (WORK_NAME with --no-claim) and BEADS_ACTOR

bd show $CLAIMED_ID

# Do the work, then run quality gates (from the worktree root)
python3 -m pytest -v -k "refactor"

git add <files>
git commit -m "<message>"
```

Run Python from the worktree root. The venv's editable install points at the primary checkout; `python3 -m pytest` and `python3 -c` put the current directory first on `sys.path`, so they import the worktree's `jedi/`. A script run as `python3 scripts/<name>.py` does not — set `PYTHONPATH=$PWD` for those.

### 3. Landing the Plane (in the worktree)

File beads for anything you noticed but didn't work on — related issues, edge cases, tangents. Do not pursue them.

```bash
bd create --title="..." --type=task --priority=<n>
```

Then run the landing script:

```bash
bash scripts/agent-land.sh
```

What it does, in order:

1. Runs the quality gates with the primary checkout's venv: `scripts/smoke_dependents.py` (with `PYTHONPATH` set to the worktree) and `python3 -m pytest -v -k "refactor"`.
2. Merges `origin/refactoring-test-coverage` and pushes `work/<id>:refactoring-test-coverage`, retrying when another instance landed first; a push that fails for any other reason stops the script. The issue stays `in_progress` until the code is on origin.
3. Closes the issue.
4. Commits a fresh `bd export` to `.beads/issues.jsonl` and pushes it, retrying the same way; then runs `bd dolt push`.
5. Removes the worktree and its branch.

A conflict in `.beads/issues.jsonl` is resolved automatically by exporting again: the file is only a snapshot of the shared database. A conflict in any other file stops the script with the worktree intact — resolve it there, commit, and re-run `agent-land.sh`. If only `bd dolt push` fails, the landing is complete in git; the script says so and exits non-zero, and `bd dolt push` should be re-run from the primary checkout.

### 4. **MANDATORY: Reflect on Workflow**

Review the session for friction, gaps, or follow-up work. This step is **not optional** — do not skip it. `agent-land.sh` removes your worktree, so reflect on startup and work *before* running it, and on the landing itself afterwards.

**For every issue you encountered or discovered (permission errors, missing steps, unclear instructions, new edge cases):**

Fix in-place (only when the fix is clear and unambiguous):
- **If `scripts/agent-start.sh` or `agent-land.sh` failed or was incomplete:** improve the script.
- **If setup instructions in AGENTS.md were wrong or missing a step:** update them.
- **If a new category of obstacle appeared:** add it to the script's guard logic.
- **If any step is currently prose instructions:** convert it to scripted commands.

Commit these fixes in your worktree before running `agent-land.sh`, so they land with your change; the next `agent-start.sh` fast-forwards them into the primary checkout. Anything found during landing has no worktree to fix it in — file a bead for it.

File a bead for anything requiring deeper investigation or design:
1. **File a bead** — `bd create --title="..." --description="..." --type=task --priority=<n>`
2. **Push any new beads** — beads filed before `agent-land.sh` are exported and pushed by it. After landing, run `bd dolt push` in the primary checkout (it pushes only the database; `.beads/issues.jsonl` catches up at the next landing).

**If workflow was smooth with no issues:** write one sentence saying so — no bead needed.

The goal: the next agent should be able to run `bash scripts/agent-start.sh`, do their work, and run `bash scripts/agent-land.sh` with no manual intervention.

**Stop after one issue.**

## Beads Database

This project runs beads in **server mode** (`"dolt_mode": "server"` in `.beads/metadata.json`, database `beads_jedi`). Beads documents its default embedded mode as single-writer — one process at a time — and server mode as the mode for multiple agents writing simultaneously. `agent-start.sh` refuses to run in any other mode.

- **Server lifecycle.** `bd` starts the `dolt sql-server` on demand from the primary checkout's `.beads/`, and it keeps running after agents exit. Stop it with `bd dolt stop` in the primary checkout when no agents are active.
- **Fresh checkout.** Start the server, then `bd bootstrap --yes`, which clones the database from the Dolt remote (`agent-start.sh` does this when `.beads/dolt/` is missing). Never use `bd init --force`: it re-initializes over existing data, and it refuses anyway once origin holds Dolt data.

Two sync paths, and landing runs both:

```bash
bd dolt push                      # full Dolt DB (history, audit trail) via refs/dolt/data on origin
bd export > .beads/issues.jsonl   # git-tracked snapshot
git add .beads/issues.jsonl
git commit -m "bd sync: ..."
git push origin <branch>:refactoring-test-coverage
```

`bd dolt push` is what `bd bootstrap` restores from, so a fresh checkout is only as current as the last push. The jsonl export keeps issue changes visible in git history and PR diffs, and `bd bootstrap` falls back to it when there is no Dolt remote.

## Why This Is Safe

- **No agent works in the primary checkout.** `agent-start.sh` only fast-forwards it and refuses when it has local changes or commits; instances push `work/<id>:refactoring-test-coverage` directly to the remote.
- **Push rejection is the coordination signal.** The loser fetches, merges, and retries in isolation.
- **`--claim` is atomic** and each instance claims under a unique actor, so exactly one instance wins per issue.
- **One server serves every writer**, which is the concurrency model beads documents for multiple agents.
- **`issues.jsonl` never needs a hand merge.** It is regenerated from the database whenever git reports a conflict in it.
