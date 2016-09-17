import re
import sys
import os
from xml.etree import ElementTree

def red(s):
    RED = '\033[31m'
    ENDC = '\033[0m'
    return RED+s+ENDC

area_template = '''\
<bean id="CENTER11" class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.Area">
</bean>
'''

cell_template = '''\
<bean id="Cell11" class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.UctoolCell">
</bean>
'''

kv_pat = re.compile(r':(?P<name>\w+)\s*=>\s*"?(?P<value>[-_0-9a-zA-Z.]+)"?')
group_pat = re.compile(r'{(.+?)}')
ltesimcli_pat = re.compile('ltesim_cli')
uepair_pat = re.compile(
    r'(?P<cnt1>\d+)\.times.*(?P<cnt2>\d+)\.times.*create_user_pair\(.*,\s*"(?P<area>\w+)"\s*\)')

ltesim_cli_cmd = None
with open(sys.argv[1]) as f:
    for line in f:
        if ltesimcli_pat.match(line):
            ltesim_cli_cmd = line

if not ltesim_cli_cmd:
    sys.exit('First file should have "ltesim_cli" command text')

ue_pair_map = dict()
with open(sys.argv[2]) as f:
    for line in f:
        m = uepair_pat.search(line)
        if m:
            area = m.group('area').upper()
            numbers = ue_pair_map.setdefault(area, [])
            numbers.append(str(int(m.group('cnt1')) * int(m.group('cnt2'))))
    

area_elem_list = []
cell_elem_list = []
for g in group_pat.finditer(ltesim_cli_cmd):
    attr_list = []  # list of dict

    is_area = is_cell = False
    for p in kv_pat.finditer(g.group(1)):
        attr_list.append(p.groupdict())
        if ('area' == p.group('name')): 
            is_area = True
        if ('cell' == p.group('name')):
            is_cell = True
    
    if is_area and is_cell:
        raise RuntimeError(red('Incorrect ltesim_cli command parameters? Found both "area" and "cell" parameter in same group'))

    # create 'area' bean
    if is_area:
        area_elem = ElementTree.fromstring(area_template)
        for attr in attr_list:
            if (attr['name'] == 'area'):
                attr['value'] = attr['value'].upper()
                area_elem.set('id', attr['value'])
            ElementTree.SubElement(area_elem, 'property', attr)

        attr = {'name': 'UEPairList'}
        uepairlist_elem = ElementTree.SubElement(area_elem, 'property', attr)        

        attr = {'parent': 'FIXME'}
        attr['p:numbers'] = ','.join(ue_pair_map.get(area_elem.get('id')))
        ElementTree.SubElement(uepairlist_elem, 'bean', attr)
        area_elem_list.append(area_elem)

    # create 'cell' bean
    if is_cell:
        cell_elem = ElementTree.fromstring(cell_template)
        for attr in attr_list:
            if (attr['name'] == 'cell'):
                cell_elem.set('id', attr['value'].capitalize())
            ElementTree.SubElement(cell_elem, 'property', attr)

        cell_elem_list.append(cell_elem)

with open('AreaMap.xml', 'w') as f:
    for elem in area_elem_list:
        f.write(re.sub(r'><', r'>\n<', ElementTree.tostring(elem)))
        f.write('\n')

with open('CellMap.xml', 'w') as f:
    for elem in cell_elem_list:
        f.write(re.sub(r'><', r'>\n<', ElementTree.tostring(elem)))
        f.write('\n')
