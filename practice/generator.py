# explore generator 

def fibonacci():
    print("fibonacci sequence")
    a = 0
    b = 1
    c = 1
    while True:
        yield c
        c = a + b
        a = b
        b = c

f = fibonacci()
for i in range(10):
    print(next(f))

# generator-iterator example
# return and receive data


def gen1():
    a = 0
    b = 0
    while(True):
        b = (yield a)
        print("receive: " + b)
        a = b + 'pick'

f = gen1()
f.send(None)
s = "return: "
print(s + f.send('1'))
print(s + f.send('2'))
print(s + f.send('10'))

# generator expression
g = (i*2 for i in range(10))
for v in g:
    print(v)

