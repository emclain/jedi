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
# -------------------------------------------------- string-value
class MyClass:
    def foo(self):
        #? 8 text
        name = "hello"
        return name
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.name = "hello"
        return self.name
# -------------------------------------------------- expression-value
class MyClass:
    def foo(self):
        #? 8 text
        result = 1 + 2 + 3
        return result
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.result = 1 + 2 + 3
        return self.result
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
# -------------------------------------------------- cls-param
class MyClass:
    @classmethod
    def foo(cls):
        #? 8 text
        x = 42
        return x + 1
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    @classmethod
    def foo(cls):
        #? 8 text
        cls.x = 42
        return cls.x + 1
# -------------------------------------------------- list-value
class MyClass:
    def foo(self):
        #? 8 text
        items = [1, 2, 3]
        return len(items)
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.items = [1, 2, 3]
        return len(self.items)
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
# -------------------------------------------------- none-value
class MyClass:
    def foo(self):
        #? 8 text
        callback = None
        if callback:
            callback()
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.callback = None
        if self.callback:
            self.callback()
# -------------------------------------------------- dict-value
class MyClass:
    def foo(self):
        #? 8 text
        config = {"key": "value"}
        return config
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.config = {"key": "value"}
        return self.config
# -------------------------------------------------- bool-value
class MyClass:
    def foo(self):
        #? 8 text
        active = True
        return active
# ++++++++++++++++++++++++++++++++++++++++++++++++++
class MyClass:
    def foo(self):
        #? 8 text
        self.active = True
        return self.active
# -------------------------------------------------- field-already-exists-error
class MyClass:
    def foo(self):
        #? 8 error
        x = 42
        self.x = 99
        return self.x
# ++++++++++++++++++++++++++++++++++++++++++++++++++
Cannot introduce a field: self.x already exists in the method
