# Python Refactoring Test Coverage Research

This document summarizes Python AST structure, tricky syntax, name resolution rules,
and other language semantics relevant to finding gaps in jedi's refactoring test
coverage. It is intended as a reference for agents auditing each refactor's tests.

---

## 1. Python AST and Assignment Variants

Jedi uses parso's CST (not `ast`), but the logical categories map directly. The
`_PRECEDENCE` table in `jedi/api/refactoring/__init__.py` covers binary operators
(`or_test` → `power`); anything outside that table is either an atom or a
higher-level construct.

### Assignment node types that matter for refactoring

| Syntax | parso node | Notes |
|---|---|---|
| `x = expr` | `expr_stmt` | Simple assignment |
| `x: T = expr` | `expr_stmt` with annotation | Annotation is preserved in rename; the name is the target |
| `x: T` | `expr_stmt` (no value) | Annotated declaration only — inline would fail ("defined by annotation") |
| `x = y = expr` | `expr_stmt` with two `=` | Inline/introduce_parameter already rejects multi-assignment |
| `x, y = expr` | `expr_stmt` with testlist_star_expr | Inline already rejects multi-name LHS |
| `x += expr` | `expr_stmt` with augassign | Inline already rejects; introduce_parameter already rejects |
| `x := expr` | `namedexpr_test` | Extract_variable already errors; rename works via walrus-var test |
| `for x in iter` | `for_stmt` | `x` is defined in enclosing scope; inline already rejects for_stmt |
| `with ctx as x` | `with_stmt` | Rename via with-as-var is covered |
| `except E as x` | `except_clause` | Rename via except-as-var is covered; note: x is *deleted* after the block |
| `[x for x in ...]` | comprehension | Inner `x` is a separate scope variable |
| `(x := expr)` | `namedexpr_test` | Leaks into enclosing scope (not comprehension scope) |

### Key gaps suggested by the above

- **`except E as x` scope deletion**: After the `except` block, `x` is deleted
  (PEP 3110). Rename inside the `except` body is tested, but renaming a variable
  that *shadows* an outer name and then gets deleted is not.
- **Annotated assignment without value** (`x: int`): Not tested for inline (should
  error "defined by annotation"), or for rename, or as the target of introduce_parameter.
- **Multiple assignment targets** (`a = b = 1`): Inline already errors; but rename
  should rename both `a` and `b` if they refer to the same definition — not tested.
- **Star unpacking** (`a, *b, c = seq`): No test for rename when cursor is on `b`
  (the starred target) or on `a`/`c`.
- **Augmented assignment** (`x += 1`): Already guarded for inline/introduce_parameter,
  but rename on an augmented-assign target (where `x` also appears on the RHS
  implicitly) is not tested.

---

## 2. Operator Precedence and Parenthesization

Jedi's `_PRECEDENCE` map (see `refactoring/__init__.py`) drives when parens are
added on inline. The table (lowest → highest) from the language reference:

```
:=  <  lambda  <  if-else  <  or  <  and  <  not  <  comparisons
    <  |  <  ^  <  &  <  << >>  <  + -  <  * / // % @
    <  unary +/-/~  <  **  <  await  <  . [] ()
```

### Tricky precedence edge cases

**Unary minus vs. `**`**
```python
-x**2   # parsed as -(x**2), not (-x)**2
```
Inlining `a = x**2` into `-a` should give `-(x**2)` — the parens are required.
No test for this interaction.

**`not` inline into `and`/`or`**
`not` has lower precedence than comparisons but the existing test (`unary-not`)
inlines `not True` into `a and b` giving `not True and b` — correct because `not`
binds more tightly than `and`. But inlining `not True` into `a or not True and b`
as the `a` sub-expression would give `not True or not True and b` — no test.

**Conditional expression (ternary)**
```python
a = x if cond else y
test(a + 1)   # → test((x if cond else y) + 1)   ← parens added, tested
```
But the other direction:
```python
a = x + 1
result = a if cond else y   # → (x + 1) if cond else y  — parens needed?
```
No test for inline where the variable is in the *condition* position of a ternary,
or in the *true/false* branches of a ternary.

**Lambda**
The existing test (`lambda-value`) inlines `lambda x: x+1` into `test(a)` →
`test(lambda x: x+1)` — correct, lambda needs no extra parens when it is the
entire argument. But inlining a lambda as one operand of a binary expression
requires parens:
```python
a = lambda x: x + 1
result = a or fallback   # → (lambda x: x + 1) or fallback
```
Not tested.

**`await` expression**
`await` is between `**` and atom_expr in precedence. Inlining an awaited value
into an expression has not been tested.

**`**` (exponentiation) right-associativity**
```python
a = 2**3
test(a**2)   # → test((2**3)**2)   — left side of ** needs parens
```
Not tested: inline where the inlined expression itself contains `**` and is placed
as the *left* operand of another `**`.

---

## 3. Comments and Whitespace

### What the tests already cover
- Inline strips inline comments to a standalone comment line (`comment` test).
- Inline handles semicolons: `a = 1, 2 ; b = 3` → the `b = 3` part is preserved.
- Extract_function preserves interior comments in range extraction.
- The `no-tree-name` test asserts trailing whitespace significance.

### Gaps

**Encoding declaration / shebang**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
x = 1
```
No test for rename/inline at the top of a file that has a shebang or encoding
comment. The refactoring must not corrupt or move line 1/2.

**Type comments** (`# type: ignore`, `# type: int`)
```python
x = []  # type: List[int]
```
Rename of `x` should preserve the `# type:` comment. Not tested.

**Inline comment on the definition line vs. the use line**
```python
a = expensive()  # side effect!
use(a)           # must not run twice
```
Inline silently duplicates the expression (the `in-function-call` test already
shows this behavior) — but there is no test that the *comment* from the definition
line is either preserved or handled sensibly when inlining with multiple uses.

**Blank lines within a class body before the extracted method**
Extract_function inserts new methods; the placement relative to blank lines between
methods is tested (in-method tests) but the case of a class with no prior methods
(empty body, only `pass`) is not.

**Decorator comment separation**
```python
# This is a module function
@decorator   # some decorator
def f(): ...
```
Extracting a range ending at the decorator line or renaming the function should
handle the comment between the decorator and def. Not tested.

---

## 4. Name Resolution (LEGB) Edge Cases

### Comprehension scope (Python 3+)
List/set/dict comprehensions and generator expressions execute in an **implicitly
nested scope**. The iteration variable does NOT leak:
```python
x = [x*2 for x in range(5)]
print(x)  # x here is the outer x (the list), not the loop var
```
- Rename test `comprehension-scope` covers renaming the *outer* `x` (LHS name).
- Rename test `comprehension-inner-var` covers renaming the loop var.
- **Gap**: renaming a name that appears in *both* a comprehension iterable and
  as a regular variable in the outer scope:
  ```python
  items = [1, 2, 3]
  result = [item for item in items]  # cursor on outer `items`
  ```
  Does rename correctly rename `items` in the iterable expression but not the
  loop variable `item`?

### Walrus operator leaks from comprehension
```python
result = [(y := x + 1) for x in range(5)]
print(y)   # y is defined in enclosing scope, not inside the comprehension
```
- Rename `walrus-var` covers the basic case.
- **Gap**: walrus inside a *nested* comprehension leaks to the *outermost enclosing
  function* scope, not the intermediate comprehension. Not tested.
- **Gap**: walrus in a dict comprehension key vs. value position.
- **Gap**: walrus used in an `if` filter:
  ```python
  result = [y for x in data if (y := transform(x)) > 0]
  ```

### Class scope does not close over
```python
x = 1
class Foo:
    y = x + 1         # x resolved from module scope ✓
    z = [x for x in range(3)]  # comprehension's 'x' is independent
```
- **Gap**: rename of a module-level name that is used inside a class body (not
  inside a method, but at class-level) — does it correctly find all references?

### `global` and `nonlocal` declarations
- `global-decl` test: renaming a global-declared name works.
- `nonlocal-rename` test: renaming a nonlocal-declared name works.
- **Gap**: renaming a variable that is declared `nonlocal` in one function but
  used normally in a sibling function (they both close over the same enclosing
  scope variable):
  ```python
  def outer():
      x = 1
      def writer():
          nonlocal x
          x = 2
      def reader():
          return x
  ```
  Renaming `x` inside `writer` should also rename in `reader`.

### Names introduced by `for` loop (persist after loop)
```python
for i in range(10):
    pass
print(i)  # i is still defined
```
- `for-loop-var` rename test covers renaming `i` including in the `print(i)` usage.
- **Gap**: renaming `i` when it appears both in a `for` loop and as an independent
  assignment before the loop (a different binding):
  ```python
  i = 0
  for i in range(10):
      pass
  ```

### Shadowing built-in names
```python
list = [1, 2, 3]
```
No rename test for renaming a name that shadows a built-in. The scope analysis
must not confuse the built-in `list` with the local `list`.

### `__all__` and module rename
When a module-level name is in `__all__`, renaming it should also update `__all__`.
No test for this.

---

## 5. Module and Import Edge Cases

### Already covered
- `import` test: rename crosses file boundary (updates the source file).
- `module` test: renaming a module name renames the file.
- `import-as-alias`: renaming `fb` (an alias) renames the aliased binding.
- `weird-package-mix`: conditional imports resolved.

### Gaps

**Relative imports**
```python
from . import sibling
from ..pkg import thing
```
No test for rename across relative imports. Does jedi correctly follow the relative
path to find the definition?

**Star imports**
```python
from os.path import *
join(...)   # name introduced by star import
```
Renaming `join` — how does jedi handle a name whose sole definition is a star import?

**`import os; os = 3` (reimport shadowing)**
Rename on the second `os` (the integer) should not rename the import. Not tested.

**`__future__` imports**
`from __future__ import annotations` changes annotation semantics globally. No test
verifies that refactoring under this import produces correct results (e.g., annotations
are treated as strings, not evaluated).

**Conditional imports**
```python
try:
    import ujson as json
except ImportError:
    import json
```
The `import-not-found` and `weird-package-mix` tests touch multi-import; the
try/except pattern is not tested.

**`importlib.import_module` (dynamic)**
Jedi likely can't follow dynamic imports; an error test confirming graceful
degradation would be informative.

---

## 6. Async / Await

### Already covered
- `async-await-bug` and `async-await-bare`: extract_function produces `async def`.
- `async-function` rename: renaming an `async def` function works.

### Gaps

**`async for` and `async with`**
```python
async def f():
    async for item in aiter():
        pass
    async with ctx() as c:
        pass
```
No extract_function test for a range that includes `async for` or `async with`
bodies. The extracted function must also be `async def`.

**`await` inline**
```python
async def f():
    a = await something()
    return a + 1
```
Inlining `a` would give `return (await something()) + 1` — `await` has precedence
above `+`, but the existing inline tests don't cover `await` expressions. No test.

**`await` in a non-async extract target**
```python
async def f():
    return await compute()
```
If the expression `await compute()` is extracted as a variable, does the tool
correctly preserve the `await`? The `async-await-bare` extract_function test covers
range extraction but not extract_variable with an `await` expression.

**`async def` in extract_variable scope**
Extracting from inside an `async def` when the extracted sub-expression contains
`await` — not tested.

---

## 7. F-Strings

### Already covered
- `fstring-var` (rename, inline): variable used inside `f'...'` is renamed/inlined.
- `fstring-subexpr-extract` (extract_variable): the sub-expression inside `{...}`
  is extracted.

### Gaps

**Nested f-string** (Python 3.12+)
```python
f"result={f'{x:.{precision}f}'}"
```
Renaming `x` or `precision` inside a nested f-string. Python 3.12 allows arbitrary
nesting.

**f-string with format spec using the same variable**
```python
width = 10
msg = f"{value:{width}}"
```
Renaming `width` — appears in the format-spec sub-expression.

**f-string with `=` for debugging** (Python 3.8+)
```python
f"{value=}"
```
`value=` is special syntax; renaming `value` should produce `f"{renamed_value=}"`.
No test.

**Multi-line f-string**
```python
msg = (
    f"first={a} "
    f"second={b}"
)
```
Rename of `a` inside a concatenated multi-line f-string.

**`!r`, `!s`, `!a` conversion flags**
```python
f"{obj!r}"
```
Extract_variable targeting the whole f-string when it contains conversion flags.

---

## 8. Type Annotations

### Already covered
- `type-annotation` (rename): `a: int = x + 1` → rename `a` → `y: int = ...`.

### Gaps

**`from __future__ import annotations`**
Under PEP 563, all annotations are treated as strings and not evaluated. Renaming
a name that appears in annotations may need to rewrite the string literal, or at
minimum not break.

**PEP 604 union syntax** (`X | Y`)
```python
def f(x: int | str) -> None: ...
```
The `|` in an annotation is a `bitor_expr`; renaming a type alias used in annotations
should follow through.

**PEP 695 type parameter syntax** (Python 3.12+)
```python
type Vector[T] = list[T]
def first[T](lst: list[T]) -> T: ...
```
`T` is a new-style type parameter. Rename of `T` within the type parameter list
and body. No test.

**Annotated assignment without value**
```python
x: int
```
- Inline: should error "defined by annotation" (no value) — no test.
- Introduce_parameter: should error since there's no value — no test.
- Rename: should work (it's still a valid name binding).

---

## 9. Decorators

### Already covered
- `in-function-with-dec`: extract_function with a `@classmethod` decorator present.
- `decorator-reference` (rename): renaming a decorator name.
- `decorator-name` (extract_variable): extracting the decorator expression.

### Gaps

**Multiple stacked decorators**
```python
@a
@b
@c
def f(): ...
```
Extract_function for the body of `f` — the new function should not inherit the
decorators. The current tests use at most one decorator.

**Decorator with arguments**
```python
@retry(times=3, delay=0.1)
def f(): ...
```
Extracting a range inside `f`. Does the extracted function omit the decorator?

**`@functools.wraps(original)` and the wrapped function**
Renaming `original` when it's also wrapped — does the rename correctly follow
through to the `@functools.wraps(original)` reference?

**Property decorator**
```python
class C:
    @property
    def x(self): return self._x
    @x.setter
    def x(self, v): self._x = v
```
Renaming `x` (the property) — should rename both the `@property def x` and the
`@x.setter def x`. Not tested.

---

## 10. Special Statement Forms

### `match`/`case` (Python 3.10+)
```python
match command:
    case "quit": quit()
    case "go" if (direction := get_direction()): move(direction)
    case _: pass
```
- Rename of `command` or `direction` (a walrus inside a guard).
- Extract_variable in a `case` body.
- No tests for any `match` syntax.

### `try`/`except`/`else`/`finally`
```python
try:
    x = risky()
except ValueError:
    x = default()
else:
    use(x)
finally:
    cleanup()
```
- `with-try-except` (extract_function): extracting from inside `except` is tested.
- **Gap**: extracting a range that spans `try` + `except` blocks together.
- **Gap**: rename of a variable that is assigned in *both* `try` and `except` and
  used in `else` and `finally`.
- **Gap**: `except*` (exception groups, Python 3.11+).

### `with` statement with multiple context managers
```python
with open('a') as f, open('b') as g:
    data = f.read() + g.read()
```
- `with-statement-range` (extract_function): single `with` is covered.
- **Gap**: multiple context managers in one `with`.
- **Gap**: parenthesized `with` (Python 3.10+):
  ```python
  with (open('a') as f, open('b') as g):
  ```

### Semicolons
```python
x = 1; y = 2; z = 3
```
- `semicolon` inline test: the non-inlined assignment is preserved correctly.
- **Gap**: rename when the target assignment is in a semicolon-separated statement
  and there are usages on the same logical line.

### `global` inside a nested function changes semantics
```python
x = 0
def f():
    def g():
        global x
        x = 1
```
Renaming the module-level `x` should chase through the `global x` in `g`.

---

## 11. Extract Function — Additional Patterns

### Multiple return values
```python
def f():
    x, y = compute()
    return x + y
```
Extracting the range `x, y = compute()` — the extracted function needs to
`return x, y` and the call site needs unpacking. No test for tuple-return extraction.

### Generator / yield
The tests (`random-yield-1`, `random-yield-2`) confirm that extraction is rejected
when `yield` is present. But there is no test for:
- Extracting a range that contains only non-yield statements from a generator function.
- `yield from` expressions.

### Exception re-raise
```python
def f():
    try:
        risky()
    except Exception as e:
        raise  # bare re-raise
```
Extracting the `try` block — the bare `raise` inside the extracted function would
be semantically wrong (no active exception). No test.

### Nested comprehension as the extracted expression
```python
result = [x*y for x in rows for y in cols]
```
Extract_variable on the whole comprehension — tested via `generator-in-call`.
But extracting *part* of a nested comprehension iterable is not tested.

### Class-level extraction
- `in-class-1`, `in-class-range-1`: extraction at class level works.
- **Gap**: extracting from a class body when there are class-level `__slots__` or
  `__annotations__` assignments.

---

## 12. Rename — Additional Patterns

### Dunder methods
```python
class Foo:
    def __init__(self): ...
    def __repr__(self): ...
```
Renaming `__init__` to something else — does jedi warn or allow it? No test.

### Built-in shadowing
```python
list = []
list.append(1)
```
Renaming local `list` to `lst` — the cursor is on `list` the local variable;
must not rename the built-in `list` in other files.

### `__all__` update
```python
__all__ = ['foo', 'bar']
def foo(): ...
```
Renaming `foo` should update the string in `__all__`. Not tested.

### Rename across `__init__.py` re-exports
```python
# pkg/__init__.py
from .mod import MyClass
```
Renaming `MyClass` in `mod.py` — should the rename follow through into the
`__init__.py` re-export? Not tested.

### Rename of `self` / `cls`
Renaming the first parameter of a method is valid Python (the `nonconventional-self-param`
test for introduce_field covers using `this` instead of `self`). No rename test
for changing `self` to `this` (or vice versa) across all methods of a class.

### Comprehension variable that shadows outer name
```python
x = 10
result = {x: x*2 for x in range(5)}
print(x)   # outer x
```
The inner `x` is a separate binding. Renaming the outer `x` (col 0) should rename
only the outer `x = 10` and `print(x)`, not the loop variable inside the comprehension.

---

## 13. Introduce Parameter — Additional Patterns

### Keyword-only parameter position
If the function already has a `*args` parameter, the new parameter must come after
`*args` (making it keyword-only). No test.

### Positional-only parameter separator `/`
If the function signature already contains `/`, the new default parameter must be
placed *after* the `/`:
```python
def f(a, b, /, c=1):
    x = 99
    return a + b + c + x
```
No test.

### Variable used before definition (would become `UnboundLocalError` trap)
```python
def f():
    print(x)
    x = 5
```
Introduce_parameter on `x = 5` when `x` is also used before assignment — would
create a situation where the parameter provides the value but the print-before-assign
behavior changes. No test.

### Dataclass / `__post_init__`
```python
@dataclass
class Foo:
    def __post_init__(self):
        x = compute()
        self.value = x
```
Introduce_parameter in `__post_init__` — the new parameter would show up in
`__post_init__`'s signature, which is unusual. No test.

---

## 14. Introduce Field — Additional Patterns

### Existing `self.x` in a *different* method
The `field-already-exists-error` test checks for `self.x` in the *same* method.
But what if `self.x` is assigned in `__init__` and the cursor is in a different
method? The tool might incorrectly allow the operation. No test.

### `__init__` specifically
```python
class C:
    def __init__(self):
        x = 10
        return  # introduce_field should produce self.x = 10
```
No test for introduce_field when the method is `__init__`.

### `cls.x` in `__init_subclass__` or `__class_getitem__`
These are classmethods with non-standard `cls` semantics. No test.

---

## 15. Inline — Additional Patterns

### Inlining into a decorator expression
```python
base = some_module.decorator
@base
def f(): ...
```
Inline `base` → `@some_module.decorator`. Not tested.

### Inlining a value that appears in its own definition (circular)
```python
x = x + 1
```
Should error (it's an augmented assignment in disguise, or a `NameError`). No test.

### Inlining a string literal with special characters
```python
path = r"C:\Users\name"
os.open(path)
```
Raw strings, byte strings, multi-line strings — inline `path`. Only `raw-string`
and `bytes-literal` are tested at top level; no test inside function bodies.

### Inlining across a `with` statement
```python
x = open('f')
with x as fh:
    data = fh.read()
```
Inline `x` → `with open('f') as fh`. Not tested.

### Inlining a variable that is used as both a positional and a keyword arg
```python
fn = str
result = fn(x, base=fn)
```
Inline `fn` — the second occurrence is a keyword argument value. Not tested.

---

*Generated by jedi-dpc (research bead). See issues jedi-1yi, jedi-5tm, jedi-3cc,
jedi-a8j, jedi-awz, jedi-ad9 for per-refactor coverage-gap analysis tasks.*
