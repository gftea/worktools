from threading import Thread

class MyThread(Thread):
    def __init__(self):
        pass


class A(object):
    def __new__(cls):
        print("A: new a object of type: " + cls.__name__)
        a = object.__new__(cls)
        a.__initialized = 0
        return a

    def __init__(self):
        print("A init")
        self.__initialized = 1

class B(A):
    def __init__(self):
        print("B: init")


    

class M(type):
    def __new__(cls, name, bases, dict_):
        dict_['x'] = 'magic'
        print("__new__ called %s (%s), namespace %s" % (name, str(bases), str(dict_)))
        # need to use super.__new__ instead of use type(...) directly otherwise __init__ will not be called
        return super(M, cls).__new__(cls, name, bases, dict_)

    def __init__(cls, name, bases, dict_):
        print("__init__ called %s (%s), namespace %s" % (name, str(bases), str(dict_)))
        

class V(B):
    __metaclass__ = M
    pass
