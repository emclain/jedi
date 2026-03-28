#!/usr/bin/env bash
# regression_test_jls.sh — Compare jedi-language-server test results between
# the released jedi and a dev checkout.
#
# Usage:
#   bash scripts/regression_test_jls.sh [DEV_JEDI_PATH]
#
# DEV_JEDI_PATH defaults to the repo root containing this script.
# Exit code: 0 if no regressions, 1 if regressions detected, 2 on setup error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEV_JEDI="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ ! -f "$DEV_JEDI/setup.cfg" ] && [ ! -f "$DEV_JEDI/pyproject.toml" ]; then
  echo "ERROR: $DEV_JEDI does not look like a jedi checkout (no setup.cfg or pyproject.toml)." >&2
  exit 2
fi

# ── Temp workspace ────────────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

JLS_DIR="$WORK_DIR/jedi-language-server"
BASELINE_VENV="$WORK_DIR/baseline-venv"
DEV_VENV="$WORK_DIR/dev-venv"
BASELINE_OUT="$WORK_DIR/baseline.txt"
DEV_OUT="$WORK_DIR/dev.txt"

echo "=== jedi-language-server regression test ==="
echo "Dev jedi: $DEV_JEDI"
echo "Work dir: $WORK_DIR"
echo ""

# ── Clone jedi-language-server ────────────────────────────────────────────────
echo "--- Cloning jedi-language-server..."
git clone --depth 1 https://github.com/pappasam/jedi-language-server "$JLS_DIR" -q

# Detect released jedi version pinned by jls
PINNED_JEDI=$(python3 -c "
import re, pathlib
text = pathlib.Path('$JLS_DIR/pyproject.toml').read_text()
m = re.search(r'jedi\s*>=?\s*([0-9.]+)', text)
print('jedi>=' + m.group(1) if m else 'jedi')
" 2>/dev/null || echo "jedi")

echo "Pinned jedi requirement: $PINNED_JEDI"
echo ""

# ── Helper: create venv, install jls deps + a specific jedi, run tests ────────
run_tests() {
  local label="$1"
  local venv="$2"
  local jedi_spec="$3"   # pip install spec: "jedi==0.19.2" or "/path/to/jedi"
  local out="$4"

  echo "--- [$label] creating venv..."
  python3 -m venv "$venv"
  # shellcheck disable=SC1090
  source "$venv/bin/activate"

  echo "--- [$label] installing dependencies..."
  pip install -q --upgrade pip
  # Install the JLS package (pulls in runtime deps including jedi)
  pip install -q "$JLS_DIR"
  # Install test deps explicitly (dependency-groups in pyproject.toml, not extras)
  pip install -q pytest python-lsp-jsonrpc PyHamcrest
  # Force our target jedi (overrides whatever jls pulled in)
  pip install -q --force-reinstall "$jedi_spec"

  local installed_jedi
  installed_jedi=$(pip show jedi 2>/dev/null | awk '/^Version:/{print $2}')
  echo "--- [$label] jedi version: $installed_jedi"

  echo "--- [$label] running tests..."
  cd "$JLS_DIR"
  python3 -m pytest tests/ -v --tb=short 2>&1 | tee "$out" || true
  deactivate
  cd - > /dev/null
}

# ── Baseline (released jedi) ──────────────────────────────────────────────────
run_tests "baseline" "$BASELINE_VENV" "$PINNED_JEDI" "$BASELINE_OUT"
echo ""

# ── Dev jedi ──────────────────────────────────────────────────────────────────
run_tests "dev" "$DEV_VENV" "$DEV_JEDI" "$DEV_OUT"
echo ""

# ── Extract sorted, non-empty pass/fail lists ─────────────────────────────────
# pytest output format: "tests/...::test_name PASSED     [ 42%]"
passed_tests() {
  grep -E '::.* PASSED' "$1" | awk '{print $1}' | sort || true
}

failed_tests() {
  grep -E '::.* (FAILED|ERROR)' "$1" | awk '{print $1}' | sort || true
}

count_lines() {
  # Count non-empty lines in a variable
  [ -z "$1" ] && echo 0 || echo "$1" | grep -c .
}

BASELINE_PASS=$(passed_tests "$BASELINE_OUT")
BASELINE_FAIL=$(failed_tests "$BASELINE_OUT")
DEV_PASS=$(passed_tests "$DEV_OUT")
DEV_FAIL=$(failed_tests "$DEV_OUT")

baseline_pass_count=$(count_lines "$BASELINE_PASS")
baseline_fail_count=$(count_lines "$BASELINE_FAIL")
dev_pass_count=$(count_lines "$DEV_PASS")
dev_fail_count=$(count_lines "$DEV_FAIL")

echo "=== Results summary ==="
echo "  Baseline : $baseline_pass_count passed, $baseline_fail_count failed"
echo "  Dev jedi : $dev_pass_count passed, $dev_fail_count failed"
echo ""

# comm requires non-empty sorted inputs; use a sentinel-free approach
# Regressions = in BASELINE_PASS ∩ DEV_FAIL
if [ -n "$BASELINE_PASS" ] && [ -n "$DEV_FAIL" ]; then
  REGRESSIONS=$(comm -12 <(printf '%s\n' $BASELINE_PASS | sort) \
                          <(printf '%s\n' $DEV_FAIL   | sort) || true)
else
  REGRESSIONS=""
fi

# Fixes = in BASELINE_FAIL ∩ DEV_PASS
if [ -n "$BASELINE_FAIL" ] && [ -n "$DEV_PASS" ]; then
  FIXES=$(comm -12 <(printf '%s\n' $BASELINE_FAIL | sort) \
                   <(printf '%s\n' $DEV_PASS      | sort) || true)
else
  FIXES=""
fi

regression_count=$(count_lines "$REGRESSIONS")
fix_count=$(count_lines "$FIXES")

if [ "$fix_count" -gt 0 ]; then
  echo "--- Newly passing (fixes): $fix_count"
  echo "$FIXES" | sed 's/^/    /'
  echo ""
fi

if [ "$regression_count" -eq 0 ]; then
  echo "✓ No regressions detected."
  exit_code=0
else
  echo "✗ REGRESSIONS DETECTED: $regression_count test(s) that passed in baseline now fail."
  echo "$REGRESSIONS" | sed 's/^/    /'
  echo ""
  exit_code=1
fi

# ── Highlight test_refactoring.py ─────────────────────────────────────────────
echo ""
echo "--- test_refactoring.py results ---"
grep 'test_refactoring' "$BASELINE_OUT" | grep -E '::.* (PASSED|FAILED|ERROR)' \
  | awk '{printf "  baseline: %s\n", $0}' || echo "  (no test_refactoring.py results in baseline)"
grep 'test_refactoring' "$DEV_OUT" | grep -E '::.* (PASSED|FAILED|ERROR)' \
  | awk '{printf "  dev:      %s\n", $0}' || echo "  (no test_refactoring.py results in dev)"

exit $exit_code
