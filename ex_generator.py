'''
Trying generator 
'''

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

print(s + f.send('1'))
print(s + f.send('2'))
print(s + f.send('10'))

# generator expression
g = (i*2 for i in range(10))
for v in g:
    print(v)
