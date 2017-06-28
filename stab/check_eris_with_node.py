import os
import sys
import requests
import json
import urlparse
import re
from utils import *

RED = '\033[31;1m'
GREEN = '\033[32;1m'
YELLOW = '\033[33;1m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
ENDC = '\033[0m'


def green(s):
    return GREEN + s + ENDC


def get_ru_url(data_dict):
    if data_dict.get("ci_2_type_name") == "RADIO_UNIT" \
       and len(data_dict.get("params_ci_2")) == 0:
        return data_dict.get("ci_url_2")
    

cell_field_list = [
    "eutrancell",
    "Cell Id",
    "Bandwidth",
    "Sector function reference",
    "Sector",
    "Cell Id Group",
    "Sub Cell Id",
    "earfcndl",
    "earfcnul"
]

def get_cell_data(data_dict):
    cell_data = []
    for k in cell_field_list:
        cell_data.append(data_dict[k]["value"])
    return cell_data

def print_cell_data(data_list):
    fmt_str = ''
    for col in zip(cell_field_list, *data_list):
        fmt_str += '|{:<%d}' % (len(max(col, key=len)) + 2)

    print green(fmt_str.format(*cell_field_list))
    for c in data_list:
        print fmt_str.format(*c)
        


cert = "/proj/stab_lmr/users/ekaiqch/tools/worktools/stab/VeriSignClass3PublicPrimaryCertificationAuthority-G5.crt"
root_url = 'https://eris.lmera.ericsson.se/api/ci'


############# 
# MAIN
############
# eNB support only
enb_name = sys.argv[1]
node_type = sys.argv[2]

request_url = os.path.join(root_url, enb_name)
print request_url

# get ERIS cell data
resp = requests.get(request_url, verify=cert)
text = resp.json()
relation_list = text.get("relation_list")
ru_url_list = map(get_ru_url, relation_list)


eris_cell_list = []
for ru_url in ru_url_list:
    if ru_url != None:
        print ru_url
        resp = requests.get(ru_url, verify=cert)
        text = resp.json()

        eris_cell_list.append(get_cell_data(text.get("params")))

        additional_cells = text.get("Multiple cell")
        if additional_cells != None:
            for c in additional_cells.get("value").values():
                eris_cell_list.append(get_cell_data(c))

# select sorting key
skey = cell_field_list.index('Sector')

print "-" * 50 + "From ERIS" + "-" * 50
print_cell_data(sorted(eris_cell_list, key=lambda x: int(x[skey]) if x[skey].isdigit() else x[skey]))


node_cell_list = []
with pmoshell(enb_name, enb_name, node_type) as p:
    p.sendline('lt all')
    p.expect(MOSHELL_PROMPT)

    p.sendline('hgetc sectorcarrier sectorfunctionref')
    p.expect(MOSHELL_PROMPT)
    carrier_sector_map = {} #carrier id is key, value is sector id
    for l in p.before.splitlines():
        m = re.match('SectorCarrier=(\d+?)\s*?;SectorEquipmentFunction=(\d+)', l)
        if m:
            carrier_sector_map[m.group(1)] = m.group(2).strip()



    p.sendline('hgetc ^eutrancell ^cellid$|dlchannelbandwidth|rfcndl|rfcnul|physicallayercellidgroup|physicallayersubcellid')
    p.expect(MOSHELL_PROMPT)
    cell_data_map =  {}
    for l in p.before.splitlines():
        m = re.match('EUtranCell.DD=(?P<cname>.+?)\s*?;(?P<cid>\d+?)\s*?;(?P<bw>\d+?)\s*?;(?P<rfcndl>\d+?)\s*?;(?P<rfcnul>\d+?)\s*?;(?P<pcid>\d+?)\s*?;(?P<pscid>\d+?)', l)
        if m:

            cell_data = []
            cell_data.append(m.group('cid'))
            cell_data.append(m.group('bw'))
            cell_data.append(m.group('pcid'))
            cell_data.append(m.group('pscid'))
            cell_data.append(m.group('rfcndl'))
            cell_data.append(m.group('rfcnul'))
            cell_data_map[m.group('cname')] = cell_data

    p.sendline('hgetc sectorcarrier reservedby')
    p.expect(MOSHELL_PROMPT)
    carrier_cell_map = {} 
    for l in p.before.splitlines():
        m = re.match('SectorCarrier=(\d+?)\s*?;.+EUtranCell.DD=(.+)', l)
        if m:
            scid = m.group(1)
            cname = m.group(2).strip()
            seid = carrier_sector_map.get(scid)
            cell_data = cell_data_map.get(cname)[:]
            cell_data.insert(0, cname)
            cell_data.insert(3, seid)
            cell_data.insert(4, scid)
            node_cell_list.append(cell_data)

print "-" * 50 + "From Node Data" + "-" * 50
print_cell_data(sorted(node_cell_list, key=lambda x: int(x[skey]) if x[skey].isdigit() else x[skey]))
