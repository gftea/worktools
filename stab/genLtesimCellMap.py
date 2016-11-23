"""
Author: ekaiqch
Date: 2016-11-23
"""

import re
import sys
import os
from argparse import ArgumentParser
from collections import OrderedDict
from Tkinter import *




KV_PATTERN = re.compile(
    r':(?P<name>\w+)\s*=>\s*"?(?P<value>[-_0-9a-zA-Z.]+)"?')
GROUP_PATTERN = re.compile(r'{(.+?)}')
LTESIMCLI_PATTERN = re.compile('ltesim_cli')
UEPAIR_PATTERN = re.compile(
    r'(?P<cnt1>\d+)\.times.*(?P<cnt2>\d+)\.times.*create_user_pair\(\s*""\s*,\s*"(?P<mobility1>\w+)"\s*,\s*"(?P<csmodel1>\w+)"\s*,\s*"(?P<psmodel1>\w+)"\s*,\s*"(?P<uetype1>\w+)"\s*,\s*"(?P<area1>\w+)"\s*,\s*"(?P<mobility2>\w+)"\s*,\s*"(?P<csmodel2>\w+)"\s*,\s*"(?P<psmodel2>\w+)"\s*,\s*"(?P<uetype2>\w+)"\s*,\s*"(?P<area2>\w+)"\s*\)')



global cvs
global southBoundMap, northBoundMap, westBoundMap, eastBoundMap
global width, height, c_width, c_height


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
    area = cvs.create_rectangle(0, 0, w, h, fill='red')
    cvs.move(area, *coord)    
    cvs.create_text(*transform_coord((west+east)/2, (north+south)/2), text=name)

def draw_cell(x, y, name="", radius=5000):
    x0, y0 = transform_coord(x-radius, y+radius)
    x1, y1 = transform_coord(x+radius, y-radius)
    cvs.create_oval(x0, y0, x1, y1)
    tx, ty = transform_coord(x - radius, y)
    cvs.create_text(tx - 12, ty, text=name, fill='magenta')
	


if __name__ == '__main__':

	ap = ArgumentParser()
	ap.add_argument('-f', dest='ltesim_cmd_file', required=True)
	ap.add_argument('-w', dest='screen_width', required=True)

	args = ap.parse_args()
	
	ltesim_cli_cmd = None
	with open(args.ltesim_cmd_file) as f:
		for line in f:
			if LTESIMCLI_PATTERN.match(line):
				ltesim_cli_cmd = line

	if not ltesim_cli_cmd:
		sys.exit('can not find valid ltesim cli configuration command')


	m = re.search(r':southBoundMap\s*=>\s*(?P<southBoundMap>\d+)', ltesim_cli_cmd)
	if (m):
		southBoundMap = int(m.group('southBoundMap'))
	m = re.search(r':westBoundMap\s*=>\s*(?P<westBoundMap>\d+)', ltesim_cli_cmd)
	if (m):
		westBoundMap = int(m.group('westBoundMap'))
	m = re.search(r':northBoundMap\s*=>\s*(?P<northBoundMap>\d+)', ltesim_cli_cmd)
	if (m):
		northBoundMap = int(m.group('northBoundMap'))
	m = re.search(r':eastBoundMap\s*=>\s*(?P<eastBoundMap>\d+)', ltesim_cli_cmd)
	if (m):
		eastBoundMap = int(m.group('eastBoundMap'))

	width = eastBoundMap - westBoundMap
	height = northBoundMap - southBoundMap
	c_width = int(args.screen_width)
	c_height = c_width * height / width
			
	master=Tk()
	cvs = Canvas(master, width=c_width, height=c_height, takefocus=True)
	cvs.pack()
		
	for g in GROUP_PATTERN.finditer(ltesim_cli_cmd):
		attr_list = []  # list of dict

		is_area = is_cell = False
		for p in KV_PATTERN.finditer(g.group(1)):
			attr_list.append(p.groupdict())
			if ('area' == p.group('name')):
				is_area = True
			if ('cell' == p.group('name')):
				is_cell = True

		if is_area and is_cell:
			raise RuntimeError('Incorrect ltesim_cli command parameters? Found both "area" and "cell" parameter in same group')

		# create 'area' map
		if is_cell:    
			cellobj = OrderedDict()
			for attr in attr_list:
				if attr['name'] == 'cell':
					cellobj['name'] = attr['value']
				if attr['name'] == 'position_X':
					cellobj['x'] = int(attr['value'])
				if attr['name'] == 'position_Y':
					cellobj['y'] = int(attr['value'])
			
			print(cellobj.items())
			draw_cell(cellobj['x'], cellobj['y'], cellobj['name'])
			
		# create 'cell' map
		if is_area:
			areaobj = OrderedDict()
			for attr in attr_list:
				if attr['name'] == 'area':
					areaobj['name'] = attr['value']
				if attr['name'] == 'southBoundary':
					areaobj['south'] = int(attr['value'])
				if attr['name'] == 'northBoundary':
					areaobj['north'] = int(attr['value'])
				if attr['name'] == 'westBoundary':
					areaobj['west'] = int(attr['value'])
				if attr['name'] == 'eastBoundary':
					areaobj['east'] = int(attr['value'])
					
			print(areaobj.items())
			draw_area(areaobj['south'], areaobj['north'], areaobj['west'], areaobj['east'], areaobj['name'])
			
	mainloop()

