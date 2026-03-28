# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Setup

```bash
# Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install jedi in development mode (with test dependencies)
pip install -e '.[testing]'

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

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds


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
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
