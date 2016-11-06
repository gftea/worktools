class A(object):

    def getsize(self):
        return self.__getbase() * 2

    def getbase(self):
        return "A"

    __getbase = getbase


class B(A):

    def getbase(self):
        return "B"

    __getbase = getbase # this would not overwrite the baseclass's method


b = B()
assert(b.getsize() == "AA")

