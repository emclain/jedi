#!/usr/bin/env python3
"""
Smoke test for jedi's public Script API.

Exercises every public Script method on representative snippets to catch
obvious API breakage in seconds before running full suites. Mirrors the
methods used by common dependents (pylsp, IPython, jupyterlab-lsp, etc.).

Usage:
    python scripts/smoke_dependents.py
"""

import sys
import jedi


def check(label, result, predicate=None):
    if predicate is not None:
        ok = predicate(result)
    else:
        ok = bool(result)
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok:
        print(f"         got: {result!r}")
    return ok


def run_smoke_tests():
    failures = 0

    # ------------------------------------------------------------------
    # Intelligence methods (used by pylsp, IPython, jupyterlab-lsp)
    # ------------------------------------------------------------------
    print("Intelligence methods:")

    src = "import os\nos.path.join("
    s = jedi.Script(src)

    # complete — IPython, pylsp, jupyterlab-lsp
    failures += not check(
        "complete: os.path. members",
        s.complete(1, len("import os")),
    )

    # infer — pylsp hover
    failures += not check(
        "infer: 'os' resolves to module",
        s.infer(1, 7),
    )

    # goto — all dependents
    failures += not check(
        "goto: 'os' jumps to definition",
        s.goto(1, 7),
    )

    # get_signatures — pylsp, IPython
    failures += not check(
        "get_signatures: os.path.join(",
        s.get_signatures(2, len("os.path.join(")),
    )

    # get_references — pylsp
    failures += not check(
        "get_references: 'os' references",
        s.get_references(1, 7),
    )

    # search — pylsp workspace symbol
    search_src = "def my_function():\n    pass\nmy_function()\n"
    failures += not check(
        "search: find 'my_function'",
        list(jedi.Script(search_src).search("my_function")),
    )

    # ------------------------------------------------------------------
    # Refactoring methods (our main change surface)
    # ------------------------------------------------------------------
    print("\nRefactoring methods:")

    rename_src = "x = 1\nprint(x)\n"
    result = jedi.Script(rename_src).rename(2, 6, new_name="y")
    failures += not check(
        "rename: x → y produces changed file",
        result.get_changed_files(),
    )

    inline_src = "x = 1\nprint(x)\n"
    result = jedi.Script(inline_src).inline(1, 0)
    failures += not check(
        "inline: x inlined into print()",
        result.get_changed_files(),
    )

    ev_src = "result = 1 + 2\nprint(result)\n"
    result = jedi.Script(ev_src).extract_variable(1, 9, new_name="total")
    failures += not check(
        "extract_variable: sub-expression → variable",
        result.get_changed_files(),
    )

    ef_src = "def foo():\n    x = 1 + 2\n    return x\n"
    result = jedi.Script(ef_src).extract_function(2, 8, new_name="compute")
    failures += not check(
        "extract_function: expression → function",
        result.get_changed_files(),
    )

    ip_src = "def foo():\n    x = 42\n    return x\n"
    result = jedi.Script(ip_src).introduce_parameter(2, 4)
    failures += not check(
        "introduce_parameter: local → default param",
        result.get_changed_files(),
    )

    if_src = "class C:\n    def foo(self):\n        x = 42\n        return x\n"
    result = jedi.Script(if_src).introduce_field(3, 8)
    failures += not check(
        "introduce_field: local → instance attribute",
        result.get_changed_files(),
    )

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    print()
    if failures:
        print(f"FAILED: {failures} check(s) failed.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_tests())
