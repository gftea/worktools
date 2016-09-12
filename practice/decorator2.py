def logger(func):
    def _logger(*args, **kwds):
        print("logger print %s" % func.__name__)
        return func(*args, **kwds)
    return _logger



class A(object):

    @logger
    def test(self):
        print("A.test")        


class B(A):

    def test(self):
        print("B.test")
        super(B, self).test()


