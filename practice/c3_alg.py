# ex1: C3 failure

class A(object):
    pass

class B(object):
    pass

class C(A, B):
    pass

class D(B, A):
    pass

try: 
    class E(C, D):
        pass

except TypeError as e:
    print("C3 failure:" + str(e))



