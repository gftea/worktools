class A(object):
    def __init__(self, aname, **kwds):
        self.__name = aname
        super(A, self).__init__(**kwds)

    def draw(self, shape, **kwds):
        self.__shape = shape
        assert not hasattr(super(A, self), 'draw')


class B(A):
    def __init__(self, bname, **kwds):
        self.__name = bname
        super(B, self).__init__(**kwds)

    def draw(self, bgcolor, **kwds):
        self.__bgcolor = bgcolor
        super(B, self).draw(**kwds)


class C(A):
    def __init__(self, cname, **kwds):
        self.__name = cname
        super(C, self).__init__(**kwds)

    def draw(self, fgcolor, **kwds):
        self.__fgcolor = fgcolor
        super(C, self).draw(**kwds)

class D(B, C):
    def __init__(self, dname, **kwds):
        self.__name = dname
        super(D, self).__init__(**kwds)

    def draw(self, dim, **kwds):
        super(D, self).draw(**kwds)

class Breaker(A):
    def draw(self, **kwds):
        print("bads!")
        super(Breaker, self).draw(**kwds)

d = D(aname="A", bname="B", cname="C", dname="D")
d.draw(dim = "3D", bgcolor = "red", fgcolor = "black", shape="rectangle")


class E(D, Breaker):
    def draw(self, **kwds):
        print("E")
        super(E,self).draw(**kwds)

e = E(aname="A", bname="B", cname="C", dname="D")
e.draw(dim = "3D", bgcolor = "red", fgcolor = "black", shape="rectangle")


