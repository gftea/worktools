import unittest


def add(a,b):
    if not a or not b:
        return 0

    return a + b

class TestCase(unittest.TestCase):
    
    def testAdd(self):
        add(0,1)
        add(1,1)
        add(1,0)


if __name__ == '__main__':
    unittest.main()


