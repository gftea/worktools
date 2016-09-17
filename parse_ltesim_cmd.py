import re
import sys
import os
from xml.etree import ElementTree

area_template = '''\
<bean id="CENTER11" class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.Area">
</bean>
'''

cell_template = '''\
<bean id="Cell11" class="com.ericsson.msran.test.stability.traffic.ltesim.interfaces.UctoolCell">
</bean>
'''

kv_pat = re.compile(r':(\w+)\s*=>\s*"?([-_0-9a-zA-Z.]+)"?')
group_pat = re.compile(r'{(.+?)}')
ltesimcli_pat = re.compile('ltesim_cli')
uepair_pat = re.compile(
    r'(\d+)\.times.*(\d+)\.times.*create_user_pair\(.*,\s*"(\w+)"\s*\)')
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
            area = m.group(3).upper()
            numbers = ue_pair_map.setdefault(area, [])
            numbers.append(str(int(m.group(1)) * int(m.group(2))))
    

areas = []
rec = []
for g in group_pat.finditer(ltesim_cli_cmd):
    prop_list = []
    for p in kv_pat.finditer(g.group(1)):
        prop_list.append(p.groups())

    # create 'area' beans
    if 'area' in dict(prop_list).keys():
        area = ElementTree.fromstring(area_template)
        for n, v in prop_list:
            if (n == 'area'):
                v = v.upper()
                area.set('id', v)
            attr = dict(zip(('name', 'value'), (n, v)))
            ElementTree.SubElement(area, 'property', attr)
        attr = {'name': 'UEPairList'}
        uepairlist_elem = ElementTree.SubElement(area, 'property', attr)
        
        attr = {'parent': 'FIXME'}
        attr['p:numbers'] = ','.join(ue_pair_map.get(area.get('id')))
        ElementTree.SubElement(uepairlist_elem, 'bean', attr)

        areas.append(area)

    # create 'cell' beans
    if 'cell' in dict(prop_list).keys():
        cell = ElementTree.fromstring(cell_template)

        for n, v in prop_list:
            if (n == 'cell'):
                cell.set('id', v.capitalize())
            attr = dict(zip(('name', 'value'), (n, v)))
            ElementTree.SubElement(cell, 'property', attr)

        rec.append(cell)

with open('AreaMap.xml', 'w') as f:
    for elem in areas:
        f.write(re.sub(r'><', r'>\n<', ElementTree.tostring(elem)))
        f.write('\n')

with open('CellMap.xml', 'w') as f:
    for elem in rec:
        f.write(re.sub(r'><', r'>\n<', ElementTree.tostring(elem)))
        f.write('\n')
