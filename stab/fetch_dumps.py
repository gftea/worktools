
#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python -u
"""
Author: ekaiqch
Date: 2016-11-23
"""


import os
import sys
from argparse import ArgumentParser
import subprocess
import glob
from utils import *
from simple_logger import *


ap = ArgumentParser()
ap.add_argument('-p', dest='ip')
ap.add_argument('-t', dest='fromtime')
ap.add_argument('-d', dest='destdir')


args = ap.parse_args()
ip = args.ip
from_time = args.fromtime
dest_dir = args.destdir


username = "root"
password = "root"
prompt = "root@.+?:[0-9a-zA-Z_\-/~.]+# \Z"

remote_dir_list = ["/rcs/dumps/appdump", "/rcs/dumps/pmd/*"]

if not len(from_time) == 10:
    sys.exit("ERROR!!! Incorrect FromTime format: {}!!!  Time format should be 10 digits : yymmddHHMM!".format(from_time))

file_info = []
for remote_dir in remote_dir_list:
    dump_file_list = []

    with pssh2(ip, username, password, prompt) as p:
        cmd = "ls -ltr --time-style=+%y%m%d%H%M " + remote_dir + " 2>/dev/null | egrep -v total | awk '{if (NF > 1 && $(NF-1) > " + from_time + ") {print $(NF)}}'"
        print(cmd)
        p.sendline(cmd)
        p.expect(prompt)
        dump_file_list = p.before.replace(cmd, '').strip().splitlines()

        if len(dump_file_list) > 0:
            cmd = "ls -ltr --time-style=+%y%m%d%H%M " + remote_dir + " 2>/dev/null | egrep -v total | awk '{if (NF > 1 && $(NF-1) > " + from_time + ") {print}}'"
            p.sendline(cmd)
            p.expect(prompt)
            file_info.append(p.before)


    for dump_file in dump_file_list:
        dump_file = os.path.join(remote_dir, dump_file)
        scp_cmd = "scp -r {}@{}:{} {}".format(username, ip, dump_file, dest_dir)
        with pexec(scp_cmd, password):
            pass

if len(file_info) > 0:
    with open(os.path.join(dest_dir, 'fetch_list.txt'), 'w') as f:
        for s in file_info:
            f.write(s)



