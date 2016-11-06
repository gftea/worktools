class MyClass(object):
    def __init__(self, id):
        self._id = id

    def _get_id(self):
        return self._id + 1

    id = property(_get_id)


t = MyClass(1)
print(t.id)
