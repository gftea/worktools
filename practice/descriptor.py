class Desc(object):
    def __init__(self):
        print("desc")

    def __get__(self, obj, cls):
        print("get desc")
        return "desc"

    def __set__(self, obj, value):
        print("set desc")

class C(object):
    d = Desc()

    def func1(self):
        """mydocs"""
        pass

    def func2(self):
        pass

class D(C):
    pass



    
