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
# -------------------------------------------------- field-already-exists-error
class MyClass:
    def foo(self):
        #? 8 error
        x = 42
        self.x = 99
        return self.x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: self.x already exists in the method
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
