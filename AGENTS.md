# Goals

I want to add to the test coverage of refactorings in jedi, finding
edge cases and seeing if there are issues that haven't been handled.

In addition, I want to expand the refactorings available, starting
with the Core 6 refactorings described by Arlo Belshee for the Read by
Refactoring method. Here is a quote from Arlo's blog:
https://arlobelshee.com/the-core-6-refactorings/

  The Core 6 refactorings are:

 -   Rename
 -   Inline
 -   Extract Method
 -   Introduce Local Variable
 -   Introduce Parameter
 -   Introduce Field

  These are the Core 6 because the most important thing we need to do
  when reading indebted code is to name it. We execute our core
  understanding loop: look at something, have an insight, write it down,
  check it in. The write it down step is always a transformation on
  names.

  CRUD for Names

  The core 6 are simply CRUD for the domain of names.

 -   Create: Introduce Local Variable, Extract Method, Introduce Parameter, Introduce Field.
 -   Read: (performed by the human; no refactoring needed)
 -   Update: Rename
 -   Delete: Inline

  In a typical refactoring IDE, Rename and Inline operate on anything
  which is namable, but there is a distinct Create operation per kind of
  thing you want to create.

  In typical OO languages, there are 4 things* we can name: local
  variables, methods, parameters, fields. There are also classes, but
  those are different. I think of variables, methods, parameters, and
  fields as scalars. They are atomic, simple things. Classes are
  compositions; they compose scalars together.

# Work Tracking

As a work tracking system, we use Beads (see instructions below)
https://github.com/steveyegge/beads
instead of unstructured markdown or Claude memory files. Start with a
plan and work your way through breaking it down into smaller pieces,
filing beads as you go.

If you find issues impeding your work, file them as beads rather than
context switching to try to fix them.

Work in small bites, file beads as you go, and push your changes
without my prompting. When you reach the end of your context window,
prefer to use beads as your memory and quit rather than compacting.

# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Beads Setup (fresh checkout)

Beads requires the `bd` CLI and a local Dolt database. On a new machine or container:

```bash
# 1. Install the bd CLI
curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
# If that requires root, download the binary directly instead:
#   ARCH=$(uname -m); [ "$ARCH" = "aarch64" ] && ARCH="arm64"
#   curl -L "https://github.com/dolthub/dolt/releases/latest/download/dolt-linux-$ARCH.tar.gz" | tar -xz -C /tmp
#   cp /tmp/dolt-linux-$ARCH/bin/dolt ~/.local/bin/

# 2. Initialize the local Dolt database from the checked-in issues.jsonl
bd init --force --prefix jedi

# 3. Import existing issues
bd import

# 4. Verify
bd list
```

> Note: the Dolt database is runtime state (not in git). You must run `bd init` + `bd import`
> on every fresh checkout or container. Export back with `bd export > .beads/issues.jsonl`
> before committing.

## Setup

```bash
# Create the virtual environment and install all dependencies (uses uv)
uv sync
source .venv/bin/activate

# Run the refactoring tests
python3 -m pytest -v -k "refactor"

# Run a single refactoring test by name
python3 -m pytest -v -k "refactor and with-try-except"
```

## Refactoring Test Format

Tests live in `test/refactor/{inline,extract_variable,extract_function,rename}.py`.
Each test has three parts separated by comment fences:

```
# -------------------------------------------------- test-name
<input code with #? marker>
# ++++++++++++++++++++++++++++++++++++++++++++++++++
<expected output>
```

The `#?` marker line is **part of the input code** (it counts as a line). Its format:

```
#? <column> [error|text] [kwargs]
```

- **column** (0-indexed): character position on the *next* line where the operation targets
- **error**: expects a `RefactoringError` — expected output is the error message
- **text**: compares the full changed source code (not a diff)
- *(omitted)*: compares a unified diff
- **kwargs**: Python dict literal, e.g. `{'new_name': 'x', 'until_column': 15}`

### Line numbering

The test parser computes `line_nr = <newlines before #?> + 2`. This is the 1-indexed
line number of the line *after* the `#?` marker. The API call is then:

```python
script.refactor_type(line_nr, column, **kwargs)
```

### Column conventions

- **inline/rename**: column points at the *name* being operated on
- **extract_variable**: column points at the start of the expression to extract;
  use `until_column` to extract a sub-expression within a line
- **extract_function**: for return expressions, column points at the expression
  after `return ` (e.g., col 11 for 4-space indent, col 15 for 8-space indent);
  for range extraction, use `until_line`/`until_column` to specify the end

### Important details

- The `#?` line itself occupies a line — `until_line` values must account for it
- Trailing whitespace in test files is significant (see `no-tree-name` test)
- Tests are parametrized and run via `test/test_integration.py::test_refactor`

## Multi-Agent Parallelism

When multiple instances are running from the same checkout, see **[MULTI_AGENT.md](MULTI_AGENT.md)**. In brief: `bash scripts/agent-start.sh` → do the work → `bash scripts/agent-land.sh`. Each agent works on exactly one issue, then stops.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull origin refactoring-test-coverage
   bd export > .beads/issues.jsonl   # persist beads state (bd dolt push is NOT configured)
   git add .beads/issues.jsonl
   git diff --cached --quiet || git commit -m "bd sync: update issues.jsonl"
   git push origin refactoring-test-coverage
   git status  # MUST show "up to date with origin"
   ```
   > **Note:** `bd dolt push` always fails in this environment — no dolt remote is configured.
   > Use `bd export > .beads/issues.jsonl` + git commit + push instead. See MULTI_AGENT.md
   > for details.
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
- Always use `git pull --no-rebase` (merge) — never `git pull --rebase`
<!-- END BEADS INTEGRATION -->
