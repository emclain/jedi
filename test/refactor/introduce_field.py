# -------------------------------------------------- simple
class MyClass:
    def foo(self):
        #? 8 text
        x = 42
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 42
        return self.x + 1
# -------------------------------------------------- multiple-references
class MyClass:
    def foo(self):
        #? 8 text
        x = 10
        a = x + 1
        b = x * 2
        return a + b + x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 10
        a = self.x + 1
        b = self.x * 2
        return a + b + self.x
# -------------------------------------------------- with-other-locals
class MyClass:
    def foo(self):
        a = 1
        #? 8 text
        x = 42
        return a + x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        a = 1
        #? 8 text
        self.x = 42
        return a + self.x
# -------------------------------------------------- nonconventional-self-param
class MyClass:
    def foo(this):
        #? 8 text
        x = 42
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(this):
        #? 8 text
        this.x = 42
        return this.x + 1
# -------------------------------------------------- in-conditional
class MyClass:
    def foo(self):
        #? 8 text
        x = 42
        if x > 0:
            return x
        return 0
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 42
        if self.x > 0:
            return self.x
        return 0
# -------------------------------------------------- not-in-class-error
def foo():
    #? 4 error
    x = 42
    return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the function is not inside a class
# -------------------------------------------------- not-a-definition-error
class MyClass:
    def foo(self):
        x = 42
        #? 15 error
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
The name is not a variable definition
# -------------------------------------------------- module-level-error
#? 0 error
x = 42
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the variable is not inside a function
# -------------------------------------------------- no-self-param-error
class MyClass:
    @staticmethod
    def foo():
        #? 8 error
        x = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the method has no self parameter
# -------------------------------------------------- args-only-param-error
class MyClass:
    def foo(*args):
        #? 8 error
        x = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the method has no self parameter
# -------------------------------------------------- kwargs-only-param-error
class MyClass:
    def foo(**kwargs):
        #? 8 error
        x = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the method has no self parameter
# -------------------------------------------------- field-already-exists-error
class MyClass:
    def foo(self):
        #? 8 error
        x = 42
        self.x = 99
        return self.x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: self.x already exists in the method
# -------------------------------------------------- field-exists-in-other-method-error
class MyClass:
    def __init__(self):
        self.x = 0
    def foo(self):
        #? 8 error
        x = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: self.x already exists in the class
# -------------------------------------------------- nested-class-var-error
def a():
    class Foo:
        #? 8 error
        b = 7
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: the variable is not inside a function
# -------------------------------------------------- deeply-nested-class
class Outer:
    class Inner:
        def foo(self):
            #? 12 text
            x = 1
            return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class Outer:
    class Inner:
        def foo(self):
            #? 12 text
            self.x = 1
            return self.x
# -------------------------------------------------- builtin-shadowing-name
class MyClass:
    def foo(self):
        #? 8 text
        list = [1, 2, 3]
        return list
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.list = [1, 2, 3]
        return self.list
# -------------------------------------------------- variable-in-loop-body
class MyClass:
    def foo(self):
        for i in range(3):
            #? 12 text
            x = i * 2
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        for i in range(3):
            #? 12 text
            self.x = i * 2
        return self.x
# -------------------------------------------------- variable-before-loop-used-in-for-body
class MyClass:
    def foo(self):
        #? 8 text
        x = 0
        for i in range(10):
            x += i
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 0
        for i in range(10):
            self.x += i
        return self.x
# -------------------------------------------------- variable-before-loop-used-in-while-body
class MyClass:
    def foo(self):
        #? 8 text
        x = 0
        while x < 10:
            x += 1
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 0
        while self.x < 10:
            self.x += 1
        return self.x
# -------------------------------------------------- inline-comment-on-assignment
class MyClass:
    def foo(self):
        #? 8 text
        x = 42  # important value
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 42  # important value
        return self.x
# -------------------------------------------------- nested-function-closure
class MyClass:
    def foo(self):
        #? 8 text
        x = 42
        def inner():
            return x
        return inner()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 42
        def inner():
            return self.x
        return inner()
# -------------------------------------------------- annotated-declaration-no-value-error
class MyClass:
    def foo(self):
        #? 8 error
        x: int
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field from an annotation without a value
# -------------------------------------------------- annotated-assignment
class MyClass:
    def foo(self):
        #? 8 text
        x: int = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x: int = 42
        return self.x
# -------------------------------------------------- variable-in-fstring
class MyClass:
    def foo(self):
        #? 8 text
        x = 'world'
        msg = f'hello {x}'
        return msg
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 'world'
        msg = f'hello {self.x}'
        return msg
# -------------------------------------------------- cls-param-init-subclass
class MyClass:
    def __init_subclass__(cls, **kwargs):
        #? 8 text
        x = 42
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def __init_subclass__(cls, **kwargs):
        #? 8 text
        cls.x = 42
        return cls.x
# -------------------------------------------------- cls-param-class-getitem
class MyClass:
    def __class_getitem__(cls, item):
        #? 8 text
        x = item
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def __class_getitem__(cls, item):
        #? 8 text
        cls.x = item
        return cls.x
# -------------------------------------------------- variable-before-try-used-in-try-except
class MyClass:
    def foo(self):
        #? 8 text
        x = 0
        try:
            x = compute()
        except ValueError:
            x = -1
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.x = 0
        try:
            self.x = compute()
        except ValueError:
            self.x = -1
        return self.x
# -------------------------------------------------- in-init-method
class MyClass:
    def __init__(self):
        #? 8 text
        x = 10
        self.value = x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def __init__(self):
        #? 8 text
        self.x = 10
        self.value = self.x + 1
# -------------------------------------------------- variable-assigned-in-except
class MyClass:
    def foo(self):
        try:
            risky()
        except RuntimeError:
            #? 12 text
            x = default()
        return x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        try:
            risky()
        except RuntimeError:
            #? 12 text
            self.x = default()
        return self.x
