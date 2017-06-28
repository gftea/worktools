import sys
import re
from const import *
from utils import *




ip=sys.argv[1]
node_type=sys.argv[2]
node_name=sys.argv[3]



with pmoshell(ip, node_name, node_type) as p:
    p.sendline('lt all')
    p.expect(MOSHELL_PROMPT)
    p.sendline('get eutrancell rfcndl')
    p.expect(MOSHELL_PROMPT)
    rfcnDl_list = p.before.splitlines()

    p.sendline('pr eutranFreqRel')
    p.expect(MOSHELL_PROMPT)
    freqRel_list = []

    for l in p.before.splitlines():
        m = re.match('\d+\s+(ENodeBFunction=1,EUtranCell.+)', l.strip())
        if m:
            freqRel_list.append(m.group(1))
            
    missing_freqRel = []
    for l in rfcnDl_list:
        if re.match('EUtranCell.+', l):
            cellMo, attr, rfcnDl = l.strip().split()
            freqRel = 'ENodeBFunction=1,{},EUtranFreqRelation={}'.format(cellMo, rfcnDl)
            if freqRel not in freqRel_list:
                missing_freqRel.append(freqRel)

    
    print("----- Below own EUtranFreqRelation are missing! ------")
    for l in missing_freqRel:
        print(l)
        

        


    
