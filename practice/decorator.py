
# ex1
def xmlrpc(in_=(), out=(type(None),)):
    def _xmlrpc(func):
        def __check_args(v, t):

            assert(len(v) == len(t))
                
            for i, j in zip(v, t):
                assert(isinstance(i, j))

        def __xmlrpc(*args, **kwargs):
            __check_args(args, in_)
            ret = func(*args, **kwargs)
            __check_args((ret,), out)
            return ret
        return __xmlrpc
    return _xmlrpc

                
@xmlrpc((int, int))
def func1(a, b):
    print("func1 input: %d, %d" % (a, b))

@xmlrpc((int,),(int,))
def func2(a):
    print("func2 input: %d" % a)
    return a*2

if __name__ == '__main__':
    func1(1, 2)
    print("func2 return: %d " % func2(1))
    
