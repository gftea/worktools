"""
Author: ekaiqch
Date: 2016-09-19
"""

import re
import sys
import os
from xml.etree import ElementTree
from xml.dom.minidom import parseString

COMMON_HEADER_TEMPLATE = '''\
<beans
    xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd http://www.springframework.org/schema/util http://www.springframework.org/schema/util/spring-util-3.0.xsd"
    xmlns:p="http://www.springframework.org/schema/p" xmlns:context="http://www.springframework.org/schema/context"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.springframework.org/schema/beans"
    xmlns:util="http://www.springframework.org/schema/util">
<!-- Needed for @PostConstruct in UBSimUEPairList --><bean class="org.springframework.context.annotation.CommonAnnotationBeanPostProcessor" />
</beans>
'''

AREA_TEMPLATE = '''\
<bean class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.Area"></bean>
'''

CELL_TEMPLATE = '''\
<bean class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.UctoolCell"></bean>
'''

UEPAIRLIST_TEMPLATE = '''\
<property name="UEPairList"><bean class="com.ericsson.msran.test.stability.traffic.ltesim.helpers.UBSimUEPairList"></bean></property>
'''

KV_PATTERN = re.compile(
    r':(?P<name>\w+)\s*=>\s*"?(?P<value>[-_0-9a-zA-Z.]+)"?')
GROUP_PATTERN = re.compile(r'{(.+?)}')
LTESIMCLI_PATTERN = re.compile('ltesim_cli')
UEPAIR_PATTERN = re.compile(
    r'(?P<cnt1>\d+)\.times.*(?P<cnt2>\d+)\.times.*create_user_pair\(.*,\s*"(?P<mobility>\w+)"\s*,\s*"(?P<csmodel>\w+)"\s*,\s*"(?P<psmodel>\w+)"\s*,\s*"(?P<uetype>\w+)"\s*,\s*"(?P<area>\w+)"\s*\)')

RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'
ENDC = '\033[0m'

USAGE = CYAN + '''
Usage:
    python parse_ltesim_cmd.py file1 file2

file1 should contain command for ltesim configuration, For example: "ltesim_cli -ni -nc configuration.rb --args ..."
file2 should contain commands for UBSim which create user pairs.

''' + ENDC


def error_color(s):
    return RED + s + ENDC


def info_color(s):
    return GREEN + s + ENDC


if (len(sys.argv)) < 3:
    sys.exit(USAGE)

ltesim_cli_cmd = None
with open(sys.argv[1]) as f:
    for line in f:
        if LTESIMCLI_PATTERN.match(line):
            ltesim_cli_cmd = line

if not ltesim_cli_cmd:
    sys.exit('First file should have "ltesim_cli" command text')

ue_pair_map = dict()
with open(sys.argv[2]) as f:
    for line in f:
        m = UEPAIR_PATTERN.search(line)
        if m:
            area = m.group('area').upper()
            ubsim_plist = ue_pair_map.setdefault(area, [])  # list of tuple
            num = str(int(m.group('cnt1')) * int(m.group('cnt2')))
            ubsim_plist.append((num, m.group('mobility'), m.group('csmodel'),
                                m.group('psmodel'), m.group('uetype')))

area_elem_list = []
cell_elem_list = []
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
        raise RuntimeError(
            error_color(
                'Incorrect ltesim_cli command parameters? Found both "area" and "cell" parameter in same group'))

    # create 'area' bean
    if is_area:
        area_elem = ElementTree.fromstring(AREA_TEMPLATE)
        for attr in attr_list:
            if (attr['name'] == 'area'):
                attr['value'] = attr['value'].upper()
                area_elem.set('id', attr['value'])
            ElementTree.SubElement(area_elem, 'property', attr)

        uepairlist_elem = ElementTree.fromstring(UEPAIRLIST_TEMPLATE)
        area_elem.append(uepairlist_elem)
        uelistbean_elem = uepairlist_elem.find('bean')

        ubsim_plist = ue_pair_map.get(area_elem.get('id'))
        ubsim_plist = zip(*ubsim_plist)

        # keep same order as ubsim_plist
        name_list = ['p:numbers', 'mobilityListUEs1', 'csModelListUEs1',
                     'profileListUEs1', 'apnListUEs1']
        for i in range(len(name_list)):
            attr = dict()
            attr['name'] = name_list[i]
            attr['value'] = ','.join(ubsim_plist[i])
            ElementTree.SubElement(uelistbean_elem, 'property', attr)

        area_elem_list.append(area_elem)

    # create 'cell' bean
    if is_cell:
        cell_elem = ElementTree.fromstring(CELL_TEMPLATE)
        for attr in attr_list:
            if (attr['name'] == 'cell'):
                cell_elem.set('id', attr['value'].capitalize())
            ElementTree.SubElement(cell_elem, 'property', attr)

        cell_elem_list.append(cell_elem)


def write_to_xml(filename, elem_list):
    doc = parseString(COMMON_HEADER_TEMPLATE)
    root = doc.documentElement

    commentnode = doc.createComment(
        'Below beans are created from "%s" and "%s" by script "%s"' %
        (sys.argv[1], sys.argv[2], sys.argv[0]))

    root.appendChild(commentnode)
    for e in elem_list:
        root.appendChild(parseString(ElementTree.tostring(e)).documentElement)

    print(info_color("Generating file: " + filename))
    with open(filename, 'w') as f:
        doc.writexml(f, addindent="    ", newl="\n")
        doc.unlink()
    print(info_color(filename + " has been created!"))


write_to_xml('AreaMap.xml', area_elem_list)
write_to_xml('CellMap.xml', cell_elem_list)
