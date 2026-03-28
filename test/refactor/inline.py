# -------------------------------------------------- no-name-error
#? 0 error
1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
There is no name under the cursor
# -------------------------------------------------- no-reference-error
#? 0 error
a = 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
There are no references to this name
# -------------------------------------------------- multi-equal-error
def test():
    #? 4 error
    a = b = 3
    return test(100, a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a statement with multiple definitions
# -------------------------------------------------- no-definition-error
#? 5 error
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
No definition found to inline
# -------------------------------------------------- multi-names-error
#? 0 error
a, b[1] = 3
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a statement with multiple definitions
# -------------------------------------------------- addition-error
#? 0 error
a = 2
a += 3
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a name with multiple definitions
# -------------------------------------------------- only-addition-error
#? 0 error
a += 3
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a statement with "+="
# -------------------------------------------------- with-annotation
foobarb: int = 1
#? 5
test(foobarb)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-foobarb: int = 1
 #? 5
-test(foobarb)
+test(1)
# -------------------------------------------------- only-annotation-error
a: int
#? 5 error
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a statement that is defined by an annotation
# -------------------------------------------------- builtin
import math
#? 7 error
math.cos
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline builtins/extensions
# -------------------------------------------------- module-error
from import_tree import inline_mod
#? 11 error
test(inline_mod)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline imports, modules or namespaces
# -------------------------------------------------- module-works
from import_tree import inline_mod
#? 22
test(x, inline_mod.  inline_var.conjugate)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- import_tree/inline_mod.py
+++ import_tree/inline_mod.py
@@ -1,2 +1 @@
-inline_var = 5 + 3
--- inline.py
+++ inline.py
@@ -1,4 +1,4 @@
 from import_tree import inline_mod
 #? 22
-test(x, inline_mod.  inline_var.conjugate)
+test(x, (5 + 3).conjugate)
# -------------------------------------------------- class
class A: pass
#? 5 error
test(A)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a class
# -------------------------------------------------- function
def foo(a):
    return a + 1
#? 5 error
test(foo(1))
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a function
# -------------------------------------------------- for-stmt
for x in []:
    #? 9 error
    test(x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline a for_stmt
# -------------------------------------------------- simple
def test():
    #? 4
    a = (30 + b, c) + 1
    return test(100, a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 def test():
     #? 4
-    a = (30 + b, c) + 1
-    return test(100, a)
+    return test(100, (30 + b, c) + 1)
# -------------------------------------------------- tuple
if 1:
    #? 4
    a = 1, 2
    return test(100, a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 if 1:
     #? 4
-    a = 1, 2
-    return test(100, a)
+    return test(100, (1, 2))
# -------------------------------------------------- multiplication-add-parens1
a = 1+2
#? 11
test(100 * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-a = 1+2
 #? 11
-test(100 * a)
+test(100 * (1+2))
# -------------------------------------------------- multiplication-add-parens2
a = 1+2
#? 11
(x, 100 * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-a = 1+2
 #? 11
-(x, 100 * a)
+(x, 100 * (1+2))
# -------------------------------------------------- multiplication-add-parens3
x
a = 1+2
#? 9
(100 ** a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 x
-a = 1+2
 #? 9
-(100 ** a)
+(100 ** (1+2))
# -------------------------------------------------- no-add-parens1
x
a = 1+2
#? 5
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 x
-a = 1+2
 #? 5
-test(a)
+test(1+2)
# -------------------------------------------------- no-add-parens2
a = 1+2
#? 9
test(3, a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-a = 1+2
 #? 9
-test(3, a)
+test(3, 1+2)
# -------------------------------------------------- no-add-parens3
a = 1|2
#? 5
(3, a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-a = 1|2
 #? 5
-(3, a)
+(3, 1|2)
# -------------------------------------------------- comment
a = 1 and 2 # foo
#? 9
(3, 3 * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,4 @@
-a = 1 and 2 # foo
+ # foo
 #? 9
-(3, 3 * a)
+(3, 3 * (1 and 2))
# -------------------------------------------------- semicolon
a = 1, 2	; b = 3
#? 9
(3, 3 == a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,4 @@
-a = 1, 2	; b = 3
+ b = 3
 #? 9
-(3, 3 == a)
+(3, 3 == (1, 2))
# -------------------------------------------------- no-tree-name
a = 1 + 2 
#? 0
a.conjugate
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
-a = 1 + 2 
 #? 0
-a.conjugate
+(1 + 2).conjugate
# -------------------------------------------------- multiple-references
def test():
    #? 4
    a = 1 + 2
    b = a + a
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 def test():
     #? 4
-    a = 1 + 2
-    b = a + a
+    b = (1 + 2) + (1 + 2)
# -------------------------------------------------- in-function-call
def test():
    #? 4
    x = foo(1, 2)
    return bar(x, x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,5 +1,4 @@
 def test():
     #? 4
-    x = foo(1, 2)
-    return bar(x, x)
+    return bar(foo(1, 2), foo(1, 2))
# -------------------------------------------------- string-value
#? 0
a = "hello world"
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = "hello world"
-test(a)
+test("hello world")
# -------------------------------------------------- multiline-expr
x
#? 0
a = (1 +
     2)
test(a * 3)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,6 +1,5 @@
 x
 #? 0
-a = (1 +
-     2)
-test(a * 3)
+test((1 +
+     2) * 3)
# -------------------------------------------------- dict-value
#? 0
a = {1: 2}
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = {1: 2}
-test(a)
+test({1: 2})
# -------------------------------------------------- list-value
#? 0
a = [1, 2, 3]
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = [1, 2, 3]
-test(a)
+test([1, 2, 3])
# -------------------------------------------------- unary-not
#? 0
a = not True
test(a and b)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = not True
-test(a and b)
+test(not True and b)
# -------------------------------------------------- conditional-expr
#? 0
a = x if cond else y
test(a + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = x if cond else y
-test(a + 1)
+test((x if cond else y) + 1)
# -------------------------------------------------- lambda-value
#? 0
a = lambda x: x + 1
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = lambda x: x + 1
-test(a)
+test(lambda x: x + 1)
# -------------------------------------------------- nested-function-scope
def outer():
    def inner():
        #? 8
        x = 42
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,6 +1,5 @@
 def outer():
     def inner():
         #? 8
-        x = 42
-        return x + 1
+        return 42 + 1
# -------------------------------------------------- import-name-error
import os
#? 0 error
os
test(os)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline imports, modules or namespaces
# -------------------------------------------------- from-import-error
from os.path import join
#? 0 error
join
test(join)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot inline imports, modules or namespaces
# -------------------------------------------------- comparison-parens
#? 0
a = 1 < 2
test(a and b)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = 1 < 2
-test(a and b)
+test(1 < 2 and b)
# -------------------------------------------------- fstring-var
#? 0
name = 'world'
msg = f'hello {name}'
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-name = 'world'
-msg = f'hello {name}'
+msg = f'hello {'world'}'
# -------------------------------------------------- set-literal
#? 0
a = {1, 2, 3}
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = {1, 2, 3}
-test(a)
+test({1, 2, 3})
# -------------------------------------------------- bytes-literal
#? 0
a = b'hello'
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = b'hello'
-test(a)
+test(b'hello')
# -------------------------------------------------- ellipsis-literal
#? 0
a = ...
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = ...
-test(a)
+test(...)
# -------------------------------------------------- raw-string
#? 0
a = r'\n\t'
test(a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = r'\n\t'
-test(a)
+test(r'\n\t')
# -------------------------------------------------- unary-minus-literal
#? 0
a = -1
test(x * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = -1
-test(x * a)
+test(x * -1)
# -------------------------------------------------- unary-minus-name
#? 0
a = -x
test(y * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = -x
-test(y * a)
+test(y * -x)
# -------------------------------------------------- attribute-access
#? 0
a = obj.attr
test(x * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = obj.attr
-test(x * a)
+test(x * obj.attr)
# -------------------------------------------------- subscript
#? 0
a = lst[0]
test(x * a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-a = lst[0]
-test(x * a)
+test(x * lst[0])
# -------------------------------------------------- kwarg-value-inline
#? 0
fn = str
result = fn(x, base=fn)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
--- inline.py
+++ inline.py
@@ -1,4 +1,3 @@
 #? 0
-fn = str
-result = fn(x, base=fn)
+result = str(x, base=str)
