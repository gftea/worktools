class MyClass(object):
    __slots__ = ['name']


class Child(MyClass):
    pass


p = MyClass()
p.name = 1
print('__dict__' in dir(p))

c = Child()
c.name = 2
print('__dict__' in dir(c))

