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


@xmlrpc((int, ), (int, ))
def func2(a):
    print("func2 input: %d" % a)
    return a*2


# ex2
from contextlib import contextmanager

@contextmanager
def logged(cls, logger):
    def _log(f):
        def __log(*args, **kwargs):
            logger(f)
            return f(*args, **kwargs)
        return __log

    for attr in dir(cls):
        if attr.startswith('_'):
            continue
        val = getattr(cls, attr)
        setattr(cls, '__logged_%s' % attr, val)
        setattr(cls, attr, _log(val))

    yield cls

    for attr in dir(cls):
        if not attr.startswith('__logged_'):
            continue
        val = getattr(cls, attr)
        setattr(cls, attr[len('__logged_'):], val)
        delattr(cls, attr)


class One(object):
    c_one = 'I am One'
    
    def _privated(self):
        pass

    def one(self, other):
        other.thing(self)

    def two(self):
        pass

class Two(object):
    def thing(self, other):
        other.two()

calls = []
def called(f):
    calls.append(f.__name__)
    
if __name__ == '__main__':
    func1(1, 2)
    print("func2 return: %d " % func2(1))

    for attr in dir(One):
        if attr.startswith('__logged'):
            print(attr)
    with logged(One, called):
        one = One()
        two = Two()
        one.one(two)
        for attr in dir(One):
            if attr.startswith('__logged'):
                print(attr)
        
    for attr in dir(One):
        if attr.startswith('__logged'):
            print(attr)
    print(calls)
