#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python

import sys, os
import re
import subprocess
import pexpect
from argparse import ArgumentParser
from contextlib import contextmanager
import getpass
from const import *
from config_parser import *
from simple_logger import *
from utils import *
from stab_test_manager import Services


server_prompt = "sekilx.+? [0-9a-zA-Z_\-/~.]+> \Z"
@contextmanager
def labserver():
    server_ip = "137.58.159.141"
    info("Login TE server {}".format(server_ip))
    username = getpass.getuser()
    exec_cmd = "ssh -X {}@{}".format(username, server_ip)
    p = pexpect.spawn(exec_cmd, timeout=1800, dimensions=TTY_WIN_SIZE)
    p.logfile_read = sys.stdout
    p.expect(server_prompt)

    yield p

    p.logfile = None
    p.logfile_read = None
    p.logfile_send = None
    p.close()



if __name__ == '__main__':

  
    hostname = os.uname()[1]
    if not re.match('sekilx.+', hostname) == None:
        sys.exit(red("The script should be run from your NX login server, like 'esekilxvXXXX' !"))

    ap = ArgumentParser()
    ap.add_argument('-u', dest='upgradepackage', required=True)
    ap.add_argument('-r', dest='revision', required=True )
    ap.add_argument('-f', dest='configfiles', required=True, nargs='+')
    ap.add_argument('-n', dest='nodename')

    args = ap.parse_args()


    upgrade_package = args.upgradepackage
    uprevison = args.revision
    node_name = args.nodename
    config_file_list = args.configfiles

  
    # parser will append data together
    for cfg_file in config_file_list: 
        cfg = parse_cfg(cfg_file)

    enb_list = cfg.enodeb_cfg_list


    serv = Services()
    with labserver() as pserver:
        print('\n')
        info("Getting UCTOOL version from MIA")
        phantomjs = "/proj/stab_lmr/ekaiqch/tools/worktools/stab/node/phantomjs-2.1.1-linux-i686/bin/phantomjs"
        cmd = "{} getUctoolVersion.js {} {}".format(phantomjs, upgrade_package, uprevison)
        uctool_release, uctool_revision = subprocess.check_output(cmd, shell=True).decode().split()
        info("UCTOOL recommended version from MIA: {} {}".format(uctool_release, uctool_revision))

        for node in enb_list:
            if node_name != None and node_name != node.node_name:
                continue
            if node.node_type == 'G2' and re.match('CXP9024418|CXP9028754', upgrade_package) == None:
                continue
            if node.node_type == 'G1' and re.match('CXP9024418|CXP9028754', upgrade_package) != None:
                continue

            print('\n')
            info('Getting version from uctool: {}'.format(node.uctool_name))
            pserver.sendline('ssh {}@{} /uctool/{}/bin/uctool.sh info'.format(node.uctool_username, node.uctool_ip, node.uctool_name))
            pserver.expect('Password: ')
            pserver.sendline(node.uctool_password)
            pserver.expect(server_prompt)
            print('\n')


            ans = ask_yes_or_no(blue("Do you want to upgrade {} to {}_{}".format(node.uctool_name, uctool_release, uctool_revision)))
            if ans == True:
                serv._install_uctool(node.uctool_ip, node.uctool_name,
                    uctool_release, uctool_revision,
                    node.uctool_username, node.uctool_password)

            moshell_cli = MOSHELL if node.node_type == 'G1' else MOSHELL2


            print('\n')
            info("Getting free disk size on: {}".format(node.node_name))
            moshell_cmd = "'vols /c'" if node.node_type == 'G1' else "'df -kh /rcs'"
            exec_cmd = '{} {} {}'.format(moshell_cli, node.node_ip, moshell_cmd)
            pserver.sendline(exec_cmd)
            pserver.expect(server_prompt)
            print('\n')

            if node.node_type == 'G2':
                info("Getting G2 UP size!")
                pserver.sendline('du -kh /proj/lterbsFtp_up/MRBS/{}-{}'.format(upgrade_package, uprevison))
                pserver.expect(server_prompt)
            else:
                info("For G1 UP, requires at least 600M on /c!")
            print('\n')            

            ans = ask_yes_or_no(blue("Is free space enough for upgrade"))
            if ans == True:
                moshell_cmd = "'run /proj/stab_lmr/git_stab/upgrade.mos'"
                exec_cmd = '{} {} {}'.format(moshell_cli, node.node_ip, moshell_cmd)
                pserver.sendline(exec_cmd)
                if node.node_type == 'G2':
                    pserver.expect("Enter upgrade package in the format.+: ")
                    pserver.sendline("{}-{}".format(upgrade_package, uprevison))
                    #pserver.expect("Do you want to upgrade with {}-{} [y/n]: ".format(upgrade_package, uprevison))
                    #pserver.sendline('y')
                else:
                    pserver.expect("What UP do you want to install?.+: ")
                    pserver.sendline("{}_{}".format(upgrade_package.replace('_','%'), uprevison))                        

                pserver.expect(server_prompt, timeout=None)

    

