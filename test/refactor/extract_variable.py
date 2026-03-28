# -------------------------------------------------- simple-1
def test():
    #? 35 text {'new_name': 'a'}
    return test(100, (30 + b, c) + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def test():
    #? 35 text {'new_name': 'a'}
    a = (30 + b, c) + 1
    return test(100, a)
# -------------------------------------------------- simple-2
def test():
    #? 25 text {'new_name': 'a'}
    return test(100, (30 + b, c) + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def test():
    #? 25 text {'new_name': 'a'}
    a = 30 + b
    return test(100, (a, c) + 1)
# -------------------------------------------------- simple-3
foo = 3.1
#? 8 text {'new_name': 'bar'}
x = int(foo + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
foo = 3.1
#? 8 text {'new_name': 'bar'}
bar = foo + 1
x = int(bar)
# -------------------------------------------------- simple-4
#? 13 text {'new_name': 'zzx.x'}
test(100, {1  |1: 2 + 3})
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 13 text {'new_name': 'zzx.x'}
zzx.x = 1  |1
test(100, {zzx.x: 2 + 3})
# -------------------------------------------------- multiline-1
def test():
    #? 30 text {'new_name': 'x'}
    return test(1, (30 + b, c) 
                            + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def test():
    #? 30 text {'new_name': 'x'}
    x = (30 + b, c) 
                                + 1
    return test(1, x)
# -------------------------------------------------- multiline-2
def test():
    #? 25 text {'new_name': 'x'}
    return test(1, (30 + b, c) 
                            + 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def test():
    #? 25 text {'new_name': 'x'}
    x = 30 + b
    return test(1, (x, c) 
                            + 1)
# -------------------------------------------------- for-param-error-1
#? 10 error {'new_name': 'x'}
def test(p1):
    return
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a name that defines something
# -------------------------------------------------- for-param-error-2
#? 12 error {'new_name': 'x'}
def test(p1= 3):
    return
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "param"
# -------------------------------------------------- for-param-1
#? 12 text {'new_name': 'x'}
def test(p1=20):
    return
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 12 text {'new_name': 'x'}
x = 20
def test(p1=x):
    return
# -------------------------------------------------- class-inheritance-1
#? 12 text {'new_name': 'x'}
class Foo(foo.Bar):
    pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 12 text {'new_name': 'x'}
x = foo.Bar
class Foo(x):
    pass
# -------------------------------------------------- class-inheritance-2
#? 16 text {'new_name': 'x'}
class Foo(foo.Bar):
    pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 16 text {'new_name': 'x'}
x = foo.Bar
class Foo(x):
    pass
# -------------------------------------------------- keyword-pass
#? 12 error {'new_name': 'x'}
def x(): pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "simple_stmt"
# -------------------------------------------------- keyword-continue
#? 5 error {'new_name': 'x'}
continue
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "simple_stmt"
# -------------------------------------------------- keyword-None
if 1:
    #? 4 text {'new_name': 'x'}
    None
# ++++++++++++++++++++++++++++++++++++++++++++++++++
if 1:
    #? 4 text {'new_name': 'x'}
    x = None
    x
# -------------------------------------------------- with-tuple
#? 4 text {'new_name': 'x'}
x +  1, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x'}
x = x +  1
x, 3
# -------------------------------------------------- range-1
#? 4 text {'new_name': 'x', 'until_column': 9}
y +  1, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 9}
x = y +  1, 3
x
# -------------------------------------------------- range-2
#? 1 text {'new_name': 'x', 'until_column': 3}
y +  1, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 1 text {'new_name': 'x', 'until_column': 3}
x = y +  1
x, 3
# -------------------------------------------------- range-3
#? 1 text {'new_name': 'x', 'until_column': 6}
y +  1, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 1 text {'new_name': 'x', 'until_column': 6}
x = y +  1
x, 3
# -------------------------------------------------- range-4
#? 1 text {'new_name': 'x', 'until_column': 1}
y +  1, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 1 text {'new_name': 'x', 'until_column': 1}
x = y
x +  1, 3
# -------------------------------------------------- addition-1
#? 4 text {'new_name': 'x', 'until_column': 9}
z = y + 1 + 2+ 3, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 9}
x = y + 1
z = x + 2+ 3, 3
# -------------------------------------------------- addition-2
#? 8 text {'new_name': 'x', 'until_column': 12}
z = y +1 + 2+ 3, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 12}
x = 1 + 2
z = y +x+ 3, 3
# -------------------------------------------------- addition-3
#? 10 text {'new_name': 'x', 'until_column': 14}
z = y + 1 + 2+ 3, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 10 text {'new_name': 'x', 'until_column': 14}
x = 1 + 2+ 3
z = y + x, 3
# -------------------------------------------------- addition-4
#? 13 text {'new_name': 'x', 'until_column': 17}
z = y + (1 + 2)+ 3, 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 13 text {'new_name': 'x', 'until_column': 17}
x = (1 + 2)+ 3
z = y + x, 3
# -------------------------------------------------- mult-add-1
#? 8 text {'new_name': 'x', 'until_column': 11}
z = foo(y+1*2+3, 3)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 11}
x = y+1
z = foo(x*2+3, 3)
# -------------------------------------------------- mult-add-2
#? 12 text {'new_name': 'x', 'until_column': 15}
z = foo(y+1*2+3)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 12 text {'new_name': 'x', 'until_column': 15}
x = 2+3
z = foo(y+1*x)
# -------------------------------------------------- mult-add-3
#? 9 text {'new_name': 'x', 'until_column': 13}
z = (y+1*2+3)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 9 text {'new_name': 'x', 'until_column': 13}
x = (y+1*2+3)
z = x
# -------------------------------------------------- extract-weird-1
#? 0 error {'new_name': 'x', 'until_column': 7}
foo = 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "expr_stmt"
# -------------------------------------------------- extract-weird-2
#? 0 error {'new_name': 'x', 'until_column': 5}
def x():
    foo = 3
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "funcdef"
# -------------------------------------------------- extract-weird-3
def x():
#? 4 error {'new_name': 'x', 'until_column': 8}
    if 1:
        pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "if_stmt"
# -------------------------------------------------- extract-weird-4
#? 4 error {'new_name': 'x', 'until_column': 7}
x = foo = 4
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a name that defines something
# -------------------------------------------------- keyword-None
#? 4 text {'new_name': 'x', 'until_column': 7}
yy = not foo or bar
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 7}
x = not foo
yy = x or bar
# -------------------------------------------------- augassign
yy = ()
#? 6 text {'new_name': 'x', 'until_column': 10}
yy += 3, 4
# ++++++++++++++++++++++++++++++++++++++++++++++++++
yy = ()
#? 6 text {'new_name': 'x', 'until_column': 10}
x = 3, 4
yy += x
# -------------------------------------------------- if-else
#? 9 text {'new_name': 'x', 'until_column': 22}
yy = foo(a if y else b)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 9 text {'new_name': 'x', 'until_column': 22}
x = a if y else b
yy = foo(x)
# -------------------------------------------------- lambda
#? 8 text {'new_name': 'x', 'until_column': 17}
y = foo(lambda x: 3, 5)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 17}
x = lambda x: 3
y = foo(x, 5)
# -------------------------------------------------- string-literal
#? 8 text {'new_name': 'msg', 'until_column': 15}
y = foo("hello")
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'msg', 'until_column': 15}
msg = "hello"
y = foo(msg)
# -------------------------------------------------- fstring-extract
#? 4 text {'new_name': 'x'}
y = f"val={a}"
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x'}
x = f"val={a}"
y = x
# -------------------------------------------------- fstring-subexpr-extract
#? 11 text {'new_name': 'x'}
y = f"val={a}"
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 11 text {'new_name': 'x'}
x = a
y = f"val={x}"
# -------------------------------------------------- fstring-nested-spec
#? 12 text {'new_name': 'p'}
y = f"{x:.{precision}f}"
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 12 text {'new_name': 'p'}
p = precision
y = f"{x:.{p}f}"
# -------------------------------------------------- dict-literal
#? 4 text {'new_name': 'x'}
y = {1: 2, 3: 4}
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x'}
x = {1: 2, 3: 4}
y = x
# -------------------------------------------------- list-literal
#? 4 text {'new_name': 'x'}
y = [1, 2, 3]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x'}
x = [1, 2, 3]
y = x
# -------------------------------------------------- nested-call
#? 8 text {'new_name': 'x'}
y = foo(bar(baz(1)))
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x'}
x = bar(baz(1))
y = foo(x)
# -------------------------------------------------- method-chain
#? 4 text {'new_name': 'x', 'until_column': 11}
y = foo.bar.baz(1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 11}
x = foo.bar
y = x.baz(1)
# -------------------------------------------------- chained-comparison
#? 4 text {'new_name': 'x', 'until_column': 13}
y = 1 < a < 10
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 13}
x = 1 < a < 10
y = x
# -------------------------------------------------- in-if-condition
if 1:
    #? 7 text {'new_name': 'x'}
    if foo(a + b):
        pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
if 1:
    #? 7 text {'new_name': 'x'}
    x = foo(a + b)
    if x:
        pass
# -------------------------------------------------- boolean-and
#? 4 text {'new_name': 'x', 'until_column': 11}
y = a and b or c
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x', 'until_column': 11}
x = a and b
y = x or c
# -------------------------------------------------- walrus-operator-error
#? 4 error {'new_name': 'x'}
(y := 3)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot extract a "walrus operator (:=)"
# -------------------------------------------------- in-function-body
def test():
    #? 8 text {'new_name': 'x'}
    return foo(a + b * c)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def test():
    #? 8 text {'new_name': 'x'}
    x = foo(a + b * c)
    return x
# -------------------------------------------------- inner-expression
#? 8 text {'new_name': 'x', 'until_column': 18}
y = foo(1 + bar(2))
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 18}
x = 1 + bar(2)
y = foo(x)
# -------------------------------------------------- negative-number
#? 4 text {'new_name': 'x'}
y = -42
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'x'}
x = -42
y = x
# -------------------------------------------------- double-star-extracts-call
#? 5 text {'new_name': 'x'}
foo(**kwargs)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 5 text {'new_name': 'x'}
x = foo(**kwargs)
x
# -------------------------------------------------- decorator-name
#? 1 text {'new_name': 'x'}
@decorator
def f(): pass
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 1 text {'new_name': 'x'}
x = decorator
@x
def f(): pass
# -------------------------------------------------- set-literal
#? 8 text {'new_name': 'x', 'until_column': 17}
y = foo({1, 2, 3})
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 17}
x = {1, 2, 3}
y = foo(x)
# -------------------------------------------------- bytes-literal
#? 8 text {'new_name': 'x', 'until_column': 16}
y = foo(b'hello')
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 8 text {'new_name': 'x', 'until_column': 16}
x = b'hello'
y = foo(x)
# -------------------------------------------------- generator-in-call
#? 4 text {'new_name': 'total'}
y = sum(x * 2 for x in range(10))
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'total'}
total = sum(x * 2 for x in range(10))
y = total
# -------------------------------------------------- ellipsis-literal
#? 4 text {'new_name': 'y'}
x = ...
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'y'}
y = ...
x = y
# -------------------------------------------------- ellipsis-in-call
#? 4 text {'new_name': 'y', 'until_column': 7}
foo(...)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 4 text {'new_name': 'y', 'until_column': 7}
y = ...
foo(y)
# -------------------------------------------------- comprehension-iterable-shadow
#? 12 text {'new_name': 'items'}
[x for x in x]
# ++++++++++++++++++++++++++++++++++++++++++++++++++
#? 12 text {'new_name': 'items'}
items = x
[x for x in items]
