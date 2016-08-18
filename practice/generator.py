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
    print(f.next())

