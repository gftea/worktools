from Tkinter import *


global c


southBoundMap = 0
northBoundMap = 32000
westBoundMap = 0
eastBoundMap = 64000



width = eastBoundMap - westBoundMap
height = northBoundMap - southBoundMap


c_width = 1024
c_height = c_width * height / width

def normalize_x(x):
    return x * c_width / width

def normalize_y(y):
    return y * c_height / height

def transform_coord(x, y):
    x_coord = normalize_x(x - westBoundMap)
    y_coord = c_height - normalize_y(y - southBoundMap)
    return x_coord, y_coord

def draw_area(south, north, west, east, name=""):
    w = normalize_x(east - west)
    h = normalize_y(north - south)
    coord = transform_coord(west, north)
    area = c.create_rectangle(0, 0, w, h, fill='yellow')
    c.move(area, *coord)    
    c.create_text(*transform_coord((west+east)/2, (north+south)/2), text=name)


def draw_cell(x, y, name="", radius=5000):
    x0, y0 = transform_coord(x-radius, y+radius)
    x1, y1 = transform_coord(x+radius, y-radius)
    c.create_oval(x0, y0, x1, y1)
    tx, ty = transform_coord(x - radius, y)
    c.create_text(tx - 12, ty, text=name, fill='cyan')
   
if __name__ == '__main__':
    master=Tk()
    c = Canvas(master, width=c_width, height=c_height, takefocus=True)
    c.pack()

    draw_area(18900, 19100, 10400, 10600, 'center11')
    draw_cell(10500, 19000, 'cell11')

    mainloop()


