# -------------------------------------------------- simple-no-params
def foo():
    #? 4 text
    x = 42
    return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=42):
    #? 4 text
    return x + 1
# -------------------------------------------------- simple-with-params
def foo(a, b):
    #? 4 text
    x = 42
    return a + b + x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(a, b, x=42):
    #? 4 text
    return a + b + x
# -------------------------------------------------- string-default
def foo():
    #? 4 text
    name = "world"
    return "hello " + name
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(name="world"):
    #? 4 text
    return "hello " + name
# -------------------------------------------------- expression-default
def foo():
    #? 4 text
    x = 1 + 2 + 3
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=1 + 2 + 3):
    #? 4 text
    return x
# -------------------------------------------------- list-default
def foo():
    #? 4 error
    items = [1, 2, 3]
    return len(items)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot use a mutable literal as a parameter default
# -------------------------------------------------- nested-function
def outer():
    def inner():
        #? 8 text
        x = 10
        return x
    return inner
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def outer():
    def inner(x=10):
        #? 8 text
        return x
    return inner
# -------------------------------------------------- rename-param
def foo():
    #? 4 text {'new_name': 'value'}
    x = 42
    return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(value=42):
    #? 4 text {'new_name': 'value'}
    return value + 1
# -------------------------------------------------- multiple-references
def foo():
    #? 4 text
    x = 10
    a = x + 1
    b = x * 2
    return a + b + x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=10):
    #? 4 text
    a = x + 1
    b = x * 2
    return a + b + x
# -------------------------------------------------- method-with-self
class MyClass:
    def foo(self):
        #? 8 text
        x = 42
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self, x=42):
        #? 8 text
        return x + 1
# -------------------------------------------------- method-with-other-params
class MyClass:
    def foo(self, a, b=10):
        #? 8 text
        x = 42
        return self.bar(a + b + x)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self, a, b=10, x=42):
        #? 8 text
        return self.bar(a + b + x)
# -------------------------------------------------- bool-default
def foo():
    #? 4 text
    verbose = True
    if verbose:
        print("hi")
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(verbose=True):
    #? 4 text
    if verbose:
        print("hi")
# -------------------------------------------------- none-default
def foo():
    #? 4 text
    callback = None
    if callback:
        callback()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(callback=None):
    #? 4 text
    if callback:
        callback()
# -------------------------------------------------- tuple-default
def foo():
    #? 4 text
    point = (1, 2)
    return point
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(point=(1, 2)):
    #? 4 text
    return point
# -------------------------------------------------- not-a-definition-error
def foo():
    x = 42
    #? 11 error
    return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
The name is not a variable definition
# -------------------------------------------------- module-level-error
#? 0 error
x = 42
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a parameter: the variable is not inside a function
# -------------------------------------------------- funcdef-error
def foo():
    #? 8 error
    def bar():
        pass
    bar()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a function as a parameter
# -------------------------------------------------- augmented-assign-error
def foo():
    x = 0
    #? 4 error
    x += 1
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a parameter from a statement with "+="
# -------------------------------------------------- lambda-default
def foo():
    #? 4 text
    fn = lambda x: x + 1
    return fn(10)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(fn=lambda x: x + 1):
    #? 4 text
    return fn(10)
# -------------------------------------------------- first-stmt-in-body
def foo():
    #? 4 text
    x = 99
    y = x + 1
    return y
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=99):
    #? 4 text
    y = x + 1
    return y
# -------------------------------------------------- middle-stmt-in-body
def foo():
    a = 1
    #? 4 text
    x = 42
    return a + x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=42):
    a = 1
    #? 4 text
    return a + x
# -------------------------------------------------- call-default
def bar():
    return 42

def foo():
    #? 4 error
    x = bar()
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot use a call expression as a default value: it would be evaluated once at definition time, not on each call
# -------------------------------------------------- call-site-unchanged
def foo():
    #? 4 text
    x = 42
    return x + 1

result = foo()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
def foo(x=42):
    #? 4 text
    return x + 1

result = foo()
# -------------------------------------------------- nested-class-var-error
def a():
    class Foo:
        #? 8 error
        b = 7
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a parameter: the variable is not inside a function
# -------------------------------------------------- star-star-kwargs-error
def foo(**kwargs):
    #? 4 error
    x = 42
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a parameter after **kwargs
# -------------------------------------------------- multiple-assignment-targets-error
def foo():
    #? 4 error
    a = b = 1
    return a + b
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a parameter from a statement with multiple definitions
