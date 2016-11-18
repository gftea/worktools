"""
ekaiqch 2016-09-23 created
"""

from xml.etree import ElementTree as ET
from xml.dom.minidom import parseString
from argparse import ArgumentParser
import re
import os
import sys


class Path(object):

    _PATH_TEMPLATE = '''\
<bean class="com.ericsson.msran.test.stability.interfaces.Path">
   <property name="wayPointDelay">
      <list>
      </list>
   </property>
   <property name="wayPointX">
      <list>
      </list>
   </property>
   <property name="wayPointY">
      <list>
      </list>
   </property>
</bean>
'''

    MSTCONFIGPATH_PATTERN = re.compile(
        r"^FORW MTE MTSCONFIGPATH\s+(?P<id>\d+)\s+(?P<num>\d+)\s*\{\s*(?P<waypoints>.+)\s*\}$",
        re.I)
    WAYPOINT_PATTERN = re.compile(r"(?P<x>-?\d+)\s+(?P<y>-?\d+)")

    def __init__(self, id):
        self._elem = ET.fromstring(
            re.sub('>\s+', '>', self._PATH_TEMPLATE, flags=re.DOTALL))
        self._elem.set('id', 'path{}'.format(id))

    @property
    def elem(self):
        return self._elem

    def add_way_point(self, x, y):
        e = ET.Element('value')
        e.text = '0'
        self._elem.find(".//*[@name='wayPointDelay']/list").append(e)
        e = ET.Element('value')
        e.text = x
        self._elem.find(".//*[@name='wayPointX']/list").append(e)
        e = ET.Element('value')
        e.text = y
        self._elem.find(".//*[@name='wayPointY']/list").append(e)


class EnbCell(object):

    MTSCONFIGENB_PATTERN = re.compile(
        r"^FORW MTE MTSCONFIGENB\s+(?P<num>\d+)\s*\{\s*(?P<enbs>.+)\s*\}$",
        re.I)
    ENB_PATTERN = re.compile(
        r"(?P<id>\d+)\s+(?P<x>-?\d+)\s+(?P<y>-?\d+)\s+(?P<num>\d+)\s*\{\s*(?P<cells>.+?)\s*\}")
    CELL_PATTERN = re.compile(
        r"(?P<id>\d+)\s+(?P<freq>\d+)\s+(?P<range>\d+)(?P<opt>.*?),")


COMMON_ROOT_TEMPLATE = '''\
<beans
    xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd http://www.springframework.org/schema/util http://www.springframework.org/schema/util/spring-util-3.0.xsd"
    xmlns:p="http://www.springframework.org/schema/p" xmlns:context="http://www.springframework.org/schema/context"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.springframework.org/schema/beans"
    xmlns:util="http://www.springframework.org/schema/util">

</beans>
'''
RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'
ENDC = '\033[0m'


def error_color(s):
    return RED + s + ENDC


def info_color(s):
    return GREEN + s + ENDC


def write_to_xml(filename, elem_list):
    doc = parseString(COMMON_ROOT_TEMPLATE)
    root = doc.documentElement

    commentnode = doc.createComment('Below beans are created from script "%s"'
                                    % (os.path.realpath(sys.argv[1])))

    root.appendChild(commentnode)
    for e in elem_list:
        root.appendChild(parseString(ET.tostring(e)).documentElement)

    print(info_color("Generating file: " + filename))
    with open(filename, 'w') as f:
        doc.writexml(f, addindent="    ", newl="\n")
        doc.unlink()
    print(info_color(filename + " has been created!"))


if __name__ == '__main__':

    arg_parser = ArgumentParser()
    arg_parser.add_argument('raw_script_file')
    args = arg_parser.parse_args()

    with open(args.raw_script_file) as f:
        path_set = set()  # for excluding duplicated paths
        path_elem_list = []
        for line in f:
            # remove comment string
            cmd, _, _ = line.partition(r"#")

            # parse and convert
            mo = Path.MSTCONFIGPATH_PATTERN.match(cmd.strip())
            if mo and mo.group('waypoints') not in path_set:
                waypoints = mo.group('waypoints')
                path_set.add(waypoints)
                path = Path(len(path_set))
                for m in Path.WAYPOINT_PATTERN.finditer(waypoints):
                    path.add_way_point(*m.groups())

                path_elem_list.append(path.elem)

        write_to_xml('Path.xml', path_elem_list)
