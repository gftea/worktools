from tkinter import *


global c

def transform(x, y):
    return (x, 600-y)

def draw_cell(north, south, west, east, name=""):
    w = east-west
    l = north-south
    coord = transform(west, north)
    cell = c.create_rectangle(0,0,w,l)
    c.move(cell, *coord)
    t = c.create_text(*transform((west+east)/2, (north+south)/2), text=name)

master=Tk()
c = Canvas(master, width=800, height=600, takefocus=True)
c.pack()

draw_cell(200,100,100,200, 'cell1')
draw_cell(400,300,100,200, 'cell2')

mainloop()


