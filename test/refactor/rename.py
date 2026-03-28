"""
Test coverage for renaming is mostly being done by testing
`Script.get_references`.
"""

# -------------------------------------------------- no-name
#? 0 error {'new_name': 'blabla'}
1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
There is no name under the cursor
# -------------------------------------------------- simple
def test1():
    #? 7 {'new_name': 'blabla'}
    test1()
    AssertionError
    return test1, test1.not_existing
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,6 +1,6 @@
-def test1():
+def blabla():
     #? 7 {'new_name': 'blabla'}
-    test1()
+    blabla()
     AssertionError
-    return test1, test1.not_existing
+    return blabla, blabla.not_existing
# -------------------------------------------------- var-not-found
undefined_var
#? 0 {'new_name': 'lala'}
undefined_var
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 undefined_var
 #? 0 {'new_name': 'lala'}
-undefined_var
+lala
# -------------------------------------------------- different-scopes
def x():
    #? 7 {'new_name': 'v'}
    some_var = 3
    some_var
def y():
    some_var = 3
    some_var
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 def x():
     #? 7 {'new_name': 'v'}
-    some_var = 3
-    some_var
+    v = 3
+    v
 def y():
     some_var = 3
     some_var
# -------------------------------------------------- keyword-param1
#? 22 {'new_name': 'lala'}
def mykeywordparam1(param1):
    str(param1)
mykeywordparam1(1)
mykeywordparam1(param1=3)
mykeywordparam1(x, param1=2)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 #? 22 {'new_name': 'lala'}
-def mykeywordparam1(param1):
-    str(param1)
+def mykeywordparam1(lala):
+    str(lala)
 mykeywordparam1(1)
-mykeywordparam1(param1=3)
-mykeywordparam1(x, param1=2)
+mykeywordparam1(lala=3)
+mykeywordparam1(x, lala=2)
# -------------------------------------------------- keyword-param2
def mykeywordparam2(param1):
    str(param1)
mykeywordparam2(1)
mykeywordparam2(param1=3)
#? 22 {'new_name': 'lala'}
mykeywordparam2(x, param1=2)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
-def mykeywordparam2(param1):
-    str(param1)
+def mykeywordparam2(lala):
+    str(lala)
 mykeywordparam2(1)
-mykeywordparam2(param1=3)
+mykeywordparam2(lala=3)
 #? 22 {'new_name': 'lala'}
-mykeywordparam2(x, param1=2)
+mykeywordparam2(x, lala=2)
# -------------------------------------------------- import
from import_tree.some_mod import foobar
#? 0 {'new_name': 'renamed'}
foobar
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- import_tree/some_mod.py
+++ import_tree/some_mod.py
@@ -1,2 +1,2 @@
-foobar = 3
+renamed = 3
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
-from import_tree.some_mod import foobar
+from import_tree.some_mod import renamed
 #? 0 {'new_name': 'renamed'}
-foobar
+renamed
# -------------------------------------------------- module
from import_tree import some_mod
#? 0 {'new_name': 'renamedm'}
some_mod
# ++++++++++++++++++++++++++++++++++++++++++++++++++
rename from import_tree/some_mod.py
rename to import_tree/renamedm.py
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
-from import_tree import some_mod
+from import_tree import renamedm
 #? 0 {'new_name': 'renamedm'}
-some_mod
+renamedm
# -------------------------------------------------- import-not-found
#? 20 {'new_name': 'lala'}
import undefined_import
haha( undefined_import)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 #? 20 {'new_name': 'lala'}
-import undefined_import
-haha( undefined_import)
+import lala
+haha( lala)
# -------------------------------------------------- in-package-with-stub
#? 31 {'new_name': 'renamedm'}
from import_tree.pkgx import pkgx
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- import_tree/pkgx/__init__.py
+++ import_tree/pkgx/__init__.py
@@ -1,3 +1,3 @@
-def pkgx():
+def renamedm():
     pass
--- import_tree/pkgx/__init__.pyi
+++ import_tree/pkgx/__init__.pyi
@@ -1,2 +1,2 @@
-def pkgx() -> int: ...
+def renamedm() -> int: ...
--- import_tree/pkgx/mod.pyi
+++ import_tree/pkgx/mod.pyi
@@ -1,2 +1,2 @@
-from . import pkgx
+from . import renamedm
--- rename.py
+++ rename.py
@@ -1,3 +1,3 @@
 #? 31 {'new_name': 'renamedm'}
-from import_tree.pkgx import pkgx
+from import_tree.pkgx import renamedm
# -------------------------------------------------- package-with-stub
#? 18 {'new_name': 'renamedp'}
from import_tree.pkgx
# ++++++++++++++++++++++++++++++++++++++++++++++++++
rename from import_tree/pkgx
rename to import_tree/renamedp
--- import_tree/pkgx/mod2.py
+++ import_tree/renamedp/mod2.py
@@ -1,2 +1,2 @@
-from .. import pkgx
+from .. import renamedp
--- rename.py
+++ rename.py
@@ -1,3 +1,3 @@
 #? 18 {'new_name': 'renamedp'}
-from import_tree.pkgx
+from import_tree.renamedp
# -------------------------------------------------- weird-package-mix
if random_undefined_variable:
    from import_tree.pkgx import pkgx
else:
    from import_tree import pkgx
#? 4 {'new_name': 'rename'}
pkgx
# ++++++++++++++++++++++++++++++++++++++++++++++++++
rename from import_tree/pkgx
rename to import_tree/rename
--- import_tree/pkgx/__init__.py
+++ import_tree/rename/__init__.py
@@ -1,3 +1,3 @@
-def pkgx():
+def rename():
     pass
--- import_tree/pkgx/__init__.pyi
+++ import_tree/rename/__init__.pyi
@@ -1,2 +1,2 @@
-def pkgx() -> int: ...
+def rename() -> int: ...
--- import_tree/pkgx/mod.pyi
+++ import_tree/rename/mod.pyi
@@ -1,2 +1,2 @@
-from . import pkgx
+from . import rename
--- import_tree/pkgx/mod2.py
+++ import_tree/rename/mod2.py
@@ -1,2 +1,2 @@
-from .. import pkgx
+from .. import rename
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 if random_undefined_variable:
-    from import_tree.pkgx import pkgx
+    from import_tree.rename import rename
 else:
-    from import_tree import pkgx
+    from import_tree import rename
 #? 4 {'new_name': 'rename'}
-pkgx
+rename
# -------------------------------------------------- decorator-reference
def my_dec(f):
    return f

#? 1 {'new_name': 'new_dec'}
@my_dec
def my_func():
    pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,8 +1,8 @@
-def my_dec(f):
+def new_dec(f):
     return f
 
 #? 1 {'new_name': 'new_dec'}
-@my_dec
+@new_dec
 def my_func():
     pass
# -------------------------------------------------- type-annotation
def f(x: int) -> str:
    #? 4 {'new_name': 'y'}
    a: int = x + 1
    return str(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 def f(x: int) -> str:
     #? 4 {'new_name': 'y'}
-    a: int = x + 1
-    return str(a)
+    y: int = x + 1
+    return str(y)
# -------------------------------------------------- comprehension-scope
#? 0 {'new_name': 'y'}
x = [x for x in range(10)]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,3 +1,3 @@
 #? 0 {'new_name': 'y'}
-x = [x for x in range(10)]
+y = [x for x in range(10)]
# -------------------------------------------------- comprehension-iterable-outer-var
#? 0 {'new_name': 'data'}
items = [1, 2, 3]
result = [items for items in items]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 #? 0 {'new_name': 'data'}
-items = [1, 2, 3]
-result = [items for items in items]
+data = [1, 2, 3]
+result = [items for items in data]
# -------------------------------------------------- global-from-function
x_var = 1
def f():
    #? 4 {'new_name': 'y_var'}
    x_var = 2
    return x_var
x_var
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 x_var = 1
 def f():
     #? 4 {'new_name': 'y_var'}
-    x_var = 2
-    return x_var
+    y_var = 2
+    return y_var
 x_var
# -------------------------------------------------- multiple-functions
def func1():
    pass
def func2():
    #? 4 {'new_name': 'new_func'}
    func1()
func1()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
-def func1():
+def new_func():
     pass
 def func2():
     #? 4 {'new_name': 'new_func'}
-    func1()
-func1()
+    new_func()
+new_func()
# -------------------------------------------------- class-method
class MyClass:
    def method(self):
        #? 13 {'new_name': 'new_method'}
        self.method()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 class MyClass:
-    def method(self):
+    def new_method(self):
         #? 13 {'new_name': 'new_method'}
-        self.method()
+        self.new_method()
# -------------------------------------------------- class-name
#? 6 {'new_name': 'NewClass'}
class OldClass:
    pass
x = OldClass()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 #? 6 {'new_name': 'NewClass'}
-class OldClass:
+class NewClass:
     pass
-x = OldClass()
+x = NewClass()
# -------------------------------------------------- nested-function
def outer():
    def inner():
        #? 8 {'new_name': 'new_inner'}
        inner()
    inner()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,6 +1,6 @@
 def outer():
-    def inner():
+    def new_inner():
         #? 8 {'new_name': 'new_inner'}
-        inner()
-    inner()
+        new_inner()
+    new_inner()
# -------------------------------------------------- fstring-var
#? 0 {'new_name': 'user'}
name = 'world'
msg = f'hello {name}'
print(name)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 #? 0 {'new_name': 'user'}
-name = 'world'
-msg = f'hello {name}'
-print(name)
+user = 'world'
+msg = f'hello {user}'
+print(user)
# -------------------------------------------------- fstring-format-spec
#? 0 {'new_name': 'w'}
width = 10
value = 3.14
result = f"{value:{width}.2f}"
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 #? 0 {'new_name': 'w'}
-width = 10
+w = 10
 value = 3.14
-result = f"{value:{width}.2f}"
+result = f"{value:{w}.2f}"
# -------------------------------------------------- except-as-var
try:
    pass
#? 21 {'new_name': 'exc'}
except ValueError as err:
    print(err)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,6 +1,6 @@
 try:
     pass
 #? 21 {'new_name': 'exc'}
-except ValueError as err:
-    print(err)
+except ValueError as exc:
+    print(exc)
# -------------------------------------------------- except-as-var-shadows-outer
x = 1
try:
    pass
#? 21 {'new_name': 'exc'}
except ValueError as x:
    print(x)
print(x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,8 +1,8 @@
-x = 1
+exc = 1
 try:
     pass
 #? 21 {'new_name': 'exc'}
-except ValueError as x:
-    print(x)
-print(x)
+except ValueError as exc:
+    print(exc)
+print(exc)
# -------------------------------------------------- global-decl
#? 0 {'new_name': 'y'}
x = 10
def f():
    global x
    x = 20
def g():
    print(x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,8 +1,8 @@
 #? 0 {'new_name': 'y'}
-x = 10
+y = 10
 def f():
-    global x
-    x = 20
+    global y
+    y = 20
 def g():
-    print(x)
+    print(y)
# -------------------------------------------------- async-function
#? 10 {'new_name': 'get_data'}
async def fetch_data():
    return 42

async def main():
    result = await fetch_data()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 #? 10 {'new_name': 'get_data'}
-async def fetch_data():
+async def get_data():
     return 42
 
 async def main():
-    result = await fetch_data()
+    result = await get_data()
# -------------------------------------------------- walrus-var
#? 11 {'new_name': 'z'}
result = [(y := x + 1) for x in range(5)]
print(y)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 #? 11 {'new_name': 'z'}
-result = [(y := x + 1) for x in range(5)]
-print(y)
+result = [(z := x + 1) for x in range(5)]
+print(z)
# -------------------------------------------------- comprehension-inner-var
#? 20 {'new_name': 'i'}
result = [x * 2 for x in range(10)]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,3 +1,3 @@
 #? 20 {'new_name': 'i'}
-result = [x * 2 for x in range(10)]
+result = [i * 2 for i in range(10)]
# -------------------------------------------------- for-loop-var
#? 4 {'new_name': 'element'}
for item in range(10):
    print(item)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 #? 4 {'new_name': 'element'}
-for item in range(10):
-    print(item)
+for element in range(10):
+    print(element)
# -------------------------------------------------- with-as-var
#? 19 {'new_name': 'handle'}
with open('f') as fh:
    data = fh.read()
    fh.close()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 #? 19 {'new_name': 'handle'}
-with open('f') as fh:
-    data = fh.read()
-    fh.close()
+with open('f') as handle:
+    data = handle.read()
+    handle.close()
# -------------------------------------------------- import-as-alias
from import_tree.some_mod import foobar as fb
result = fb + 1
#? 0 {'new_name': 'alias'}
fb
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- import_tree/some_mod.py
+++ import_tree/some_mod.py
@@ -1,2 +1,2 @@
-foobar = 3
+alias = 3
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
-from import_tree.some_mod import foobar as fb
-result = fb + 1
+from import_tree.some_mod import foobar as alias
+result = alias + 1
 #? 0 {'new_name': 'alias'}
-fb
+alias
# -------------------------------------------------- nonlocal-rename
x = 10
def inner():
    nonlocal x
    #? 4 {'new_name': 'y'}
    x = 20
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
-x = 10
+y = 10
 def inner():
-    nonlocal x
+    nonlocal y
     #? 4 {'new_name': 'y'}
-    x = 20
-    return x
+    y = 20
+    return y
# -------------------------------------------------- shadow-builtin
def shadow():
    #? 4 {'new_name': 'lst'}
    list = []
    list.append(1)
    return list
other = list(range(3))
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 def shadow():
     #? 4 {'new_name': 'lst'}
-    list = []
-    list.append(1)
-    return list
+    lst = []
+    lst.append(1)
+    return lst
 other = list(range(3))
# -------------------------------------------------- except-as-shadows-outer
x = 'outer'
try:
    pass
#? 21 {'new_name': 'exc'}
except ValueError as x:
    print(x)
print(x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,8 +1,8 @@
-x = 'outer'
+exc = 'outer'
 try:
     pass
 #? 21 {'new_name': 'exc'}
-except ValueError as x:
-    print(x)
-print(x)
+except ValueError as exc:
+    print(exc)
+print(exc)
# -------------------------------------------------- comprehension-iterable-outer-var
#? 0 {'new_name': 'items'}
x = [1, 2, 3]
result = [x for x in x]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,4 +1,4 @@
 #? 0 {'new_name': 'items'}
-x = [1, 2, 3]
-result = [x for x in x]
+items = [1, 2, 3]
+result = [x for x in items]
# -------------------------------------------------- class-body-module-var
#? 0 {'new_name': 'module_val'}
module_var = 42
class Foo:
    bar = module_var + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,5 +1,5 @@
 #? 0 {'new_name': 'module_val'}
-module_var = 42
+module_val = 42
 class Foo:
-    bar = module_var + 1
+    bar = module_val + 1
# -------------------------------------------------- nonlocal-sibling-closures
def outer():
    x = 1
    def writer():
        #? 17 {'new_name': 'y'}
        nonlocal x
        x = 2
    def reader():
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,9 +1,9 @@
 def outer():
-    x = 1
+    y = 1
     def writer():
         #? 17 {'new_name': 'y'}
-        nonlocal x
-        x = 2
+        nonlocal y
+        y = 2
     def reader():
-        return x
+        return y
# -------------------------------------------------- global-decl-nested
#? 0 {'new_name': 'y'}
x = 0
def f():
    def g():
        global x
        x = 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,7 +1,7 @@
 #? 0 {'new_name': 'y'}
-x = 0
+y = 0
 def f():
     def g():
-        global x
-        x = 1
+        global y
+        y = 1
# -------------------------------------------------- property-setter-rename
class Foo:
    @property
    #? 8 {'new_name': 'value'}
    def x(self):
        return self._x
    @x.setter
    def x(self, v):
        self._x = v
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- rename.py
+++ rename.py
@@ -1,9 +1,9 @@
 class Foo:
     @property
     #? 8 {'new_name': 'value'}
-    def x(self):
+    def value(self):
         return self._x
-    @x.setter
-    def x(self, v):
+    @value.setter
+    def value(self, v):
         self._x = v
