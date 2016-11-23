#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python

import sys
import os
import subprocess
from multiprocessing import Process
from argparse import ArgumentParser
import pexpect
import time
import re

# app modules
from config_parser import *
from simple_logger import *
from const import *
from utils import *



class Services(object):

    _registered_services = ServicesRegistery()

    def _do_actions(self, p, actionslist, prompt):
        for act in actionslist:
            p.sendline(act)
            p.expect(prompt)


    def _login_node(self, node_name, node_ip, node_type='G1'):
        """
        moshell to node and leave it in interactive mode
        """
        with pmoshell(node_ip, node_name, node_type, is_interact=True) as p:
            p.logfile_read = sys.stdout
            p.sendline('lt all')
            p.expect(".*> ")


    def _login_uctool(self, name, ip, usrname, passwd):
        """
        ssh to uctool server and leave it in interactive mode
        """
        with pssh(ip, name, usrname, passwd, is_interact=True) as p:
            p.logfile_read = sys.stdout
            actionslist = [
                "cd /uctool/{}/bin".format(name),
                "./uctool.sh info"
            ]
            self._do_actions(p, actionslist, SSH_PROMPT)

    def _login_ltesim(self, name, ip, usrname, passwd):
        """
        ssh to ltesim server and leave it in interactive mode
        """
        with pssh(ip, name, usrname, passwd, is_interact=True) as p:
            p.logfile_read = sys.stdout

            actionslist = [
                "rpm -qa | egrep 'ltesim|lctool'"
            ]
            self._do_actions(p, actionslist, SSH_PROMPT)

    def _get_node_version(self, name, ip, node_type):
        with pmoshell(ip, name, node_type) as p:
            p.sendline('cvcu')
            p.expect(MOSHELL_PROMPT)
            m = re.search('(==.*)', p.before, re.DOTALL)
            print('\n' + '=*' * 30 + name + '=*' * 30)
            print(m.group(1))

    def _get_uctool_version(self, name, ip, usrname, passwd):
        with pssh(ip, name, usrname, passwd) as p:
            p.sendline("/uctool/{}/bin/uctool.sh info".format(name))
            p.expect(SSH_PROMPT)
            m = re.search('Installed from:\s+(\S+)', p.before)
            print('\n' + '=*' * 30 + name + '=*' * 30)
            print(m.group(1))
       

    def _get_ltesim_version(self, name, ip, usrname, passwd):
        with pssh(ip, name, usrname, passwd) as p:
            p.sendline("rpm -qa | egrep 'ltesim|lctool'")
            p.expect(SSH_PROMPT)
            m = re.search('(ltesim-.+?)\r\n', p.before)
            print('\n' + '=*' * 30 + name + '=*' * 30)
            print(m.group(1))


    def _kill_ltesim(self, name, ip, usrname, passwd):
        with pssh(ip, name, usrname, passwd) as p:
            p.logfile_read = sys.stdout
            actionslist = [
                "ltesim_cli -nc",
                "kill_all"
            ]
            self._do_actions(p, actionslist, "ltesim> ")
            p.sendline("exit")
            p.expect(SSH_PROMPT)




    def _run_mo_actions(self, p, actionslist):
        """
        run moshell commands sequentially 
        """

        for action in actionslist:
            p.sendline(action)
            i = p.expect([MOSHELL_PROMPT, '\[y/n\] \? '])
            if i == 1:
                p.sendline('y')
                p.expect(MOSHELL_PROMPT)


    def _set_cv_and_restart(self,
                            node_ip,
                            node_name,
                            cv_name,
                            node_type='G1',
                            is_save_cv=True):
        """
        set cv and restart the node
        """
        info("Start to set cv and restart on node: {}".format(node_name))

        actionslist = [
            'lt all',
            'cvset {}'.format(cv_name), 
            'confbld+',
            'accn 0 manualRestart 2 0 0', 
            'pol'
        ]

        if node_type == 'G2':
            actionslist = [
                'lt all', 
                'cvre {}'.format(cv_name)
            ]

        if is_save_cv:
            saved_cvname = 'autocreated_by_stab_test_script'
            extra_actions = ['cvrm {}'.format(saved_cvname), 
                             'cvms {}'.format(saved_cvname)]
            actionslist = extra_actions + actionslist

        with pmoshell(node_ip, node_name, node_type) as p:
            self._run_mo_actions(p, actionslist)

        info("CV is set and restart done on node: {}".format(node_name))


    def _install_uctool(self, ip, name, release, revision, usrname, passwd):
        cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --uctool {rel} {rev} --user {usrname} --server {ip} --uctoolnames "{name}" uctoolinstall'.format(
            rel=release, rev=revision, usrname=usrname, ip=ip, name=name)

        with pexec(cmd, passwd):
            info("Installation done on uctool: {}".format(name))


    def _install_ltesim(self, ip, name, revision, usrname, passwd):
        cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --ltesim {rev} --user {usrname} --server {ip} rpminstall'.format(
            rev=revision, usrname=usrname, ip=ip)

        with pexec(cmd, passwd):
            info("Installation done on ltesim: {}".format(name))


    @service
    def set_baseline(self, node_list, ltesim, **kwargs):
        process_list = []

        doit = ask_yes_or_no("Install '{}' on ltesim: {}".format(
            ltesim.revision, ltesim.name))
        if doit:
            p = Process(
                target=self._install_ltesim,
                args=(ltesim.ip, ltesim.name, ltesim.revision, ltesim.username,
                      ltesim.password))
            process_list.append(p)

        for node in node_list:
            doit = ask_yes_or_no(
                "Install 'it{}_{}' on uctool: {} ({})".format(
                    node.uctool_release, node.uctool_revision,
                    node.uctool_name, node.node_name))
            if doit:
                p = Process(
                    target=self._install_uctool,
                    args=(node.uctool_ip, node.uctool_name,
                          node.uctool_release, node.uctool_revision,
                          node.uctool_username, node.uctool_password))
                process_list.append(p)

            doit = ask_yes_or_no("Set cv '{}' on node: {}".format(
                node.node_cv, node.node_name))

            if doit:
                is_save_cv = ask_yes_or_no("Do you want to save a cv first on node: {}".format(node.node_name))
                p = Process(
                    target=self._set_cv_and_restart,
                    args=(node.node_ip, node.node_name, node.node_cv, node.node_type,
                          is_save_cv))
                process_list.append(p)

        # start all tasks and wait until all finished
        for p in process_list:
            p.start()
        for p in process_list:
            p.join()

    @service
    def get_version(self, node_list, ltesim, **kwargs):
        for node in node_list:
            self._get_node_version(node.node_name, node.node_ip, node.node_type)
            self._get_uctool_version(node.uctool_name, node.uctool_ip, node.uctool_username, node.uctool_password)

        self._get_ltesim_version(ltesim.name, ltesim.ip, ltesim.username, ltesim.password)

    @service
    def start_operation(self, node_list, ltesim, **kwargs):
        main_script = os.path.abspath(__file__)
        filename = kwargs['filename']

        exec_cmd = 'gnome-terminal --geometry=180x50+30+30 -t {name} -e "python {script} -t ltesim -f {fname} -o {name}"'.format(
            script=main_script, name=ltesim.name, fname=filename)
        info(exec_cmd)
        subprocess.Popen(exec_cmd, shell=True)

        for node in node_list:
            exec_cmd = 'gnome-terminal --geometry=180x50+30+30 -t {name} -e "python {script} -t uctool -f {fname} -o {name}"'.format(
                script=main_script, name=node.uctool_name, fname=filename)
            info(exec_cmd)
            subprocess.Popen(exec_cmd, shell=True)

            exec_cmd = 'gnome-terminal --geometry=180x50+30+30 -t {name} -e "python {script} -t node -f {fname} -o {name}"'.format(
                script=main_script, name=node.node_name, fname=filename)
            info(exec_cmd)
            subprocess.Popen(exec_cmd, shell=True)

    def _recover(self, node_ip, node_name, node_type, uctool_ip, uctool_name,
                 usrname, passwd):
        """
        1. block uctool cells and stop uctool
        2. cold restart node
        3. block uctool cells
        4. restart uctool and wait for CELL_SETUP in log 
        5. deblock uctool cells
        """
        with pmoshell(node_ip, node_name, node_type) as pnode:
            with pssh(uctool_ip, uctool_name, usrname, passwd) as puctool:

                pnode.logfile_read = sys.stdout
                puctool.logfile_read = sys.stdout

                info("Blocking uctool cells on: {}".format(node_name))
                actionslist = [
                    "lt all",
                    "ma simcells cell simulated true",
                    "bl simcells"
                ]
                self._run_mo_actions(pnode, actionslist)


                info("Stopping uctool: {}".format(uctool_name))
                actionslist = [
                    "cd /uctool/{}/bin".format(uctool_name),
                    "./uctool.sh stop"
                ]
                self._do_actions(puctool, actionslist, SSH_PROMPT)

                sleep_time = 60
                info("Waiting for {} seconds before continue".format(sleep_time))
                time.sleep(sleep_time)
        
                info("Cold restarting the node: {}".format(node_name))
                restart_cmd = "accn 0 manualRestart 2 0 0" if node_type == 'G1' else "accn FieldReplaceableUnit=1$ restartUnit 1 0 0"
                actionslist = ["lt all", "confbld+", restart_cmd, "pol 10 60"]
                self._run_mo_actions(pnode, actionslist)


                info("Blocking simulated cells on node: {}".format(node_name))
                actionslist = [
                    "st simcells",
                    "wait 120",
                    "bl simcells",
                    "wait 60",
                    "st simcells"
                ]
                self._run_mo_actions(pnode, actionslist)

                info("Restartng uctool: {}".format(uctool_name))     
                puctool.sendline('./uctool.sh restart')
                puctool.expect(SSH_PROMPT)
                m = re.search("udplogger.sh: (.+?/udplogger.log) created", puctool.before)
                uctool_logfile = m.group(1)
                search_keywords = 'WAITING_FOR_CELL_SETUP'

                info("searching {} in {}".format(search_keywords, uctool_logfile))
                for i in range(30):
                    time.sleep(10)
                    puctool.sendline('grep {} {}'.format(search_keywords,uctool_logfile))
                    puctool.expect(SSH_PROMPT)
                    m = re.search("_"+search_keywords, puctool.before)
                    if m != None:
                        info("{} found in {}!".format(search_keywords, uctool_logfile))
                        break
                else:
                    raise RuntimeError(red("Timeout waiting for CELL_SETUP on uctool {}".format(uctool_name)))

                sleep_time = 60
                info("Waiting for {} seconds before continue".format(sleep_time))
                time.sleep(sleep_time)

                info("Deblocking simulated cells on node: {}".format(node_name))
                actionslist = ["deb simcells", "wait 120", "st simcells"]
                self._run_mo_actions(pnode, actionslist)
                time.sleep(1)


    @service
    def start_recovery(self, node_list, *args, **kwargs):
        process_list = []
        for node in node_list:
            is_do_recovery = ask_yes_or_no(
                "Do you want to run recovery on: {}/{}".format(
                    node.node_name, node.uctool_name))
            if is_do_recovery:
                p = Process(
                    target=self._recover,
                    args=(node.node_ip, node.node_name, node.node_type,
                          node.uctool_ip, node.uctool_name,
                          node.uctool_username, node.uctool_password))
                process_list.append(p)

        # start all actions and wait until all finished
        if len(process_list) != 0:
            ltesim = args[0]
            self._kill_ltesim(ltesim.name, ltesim.ip, ltesim.username, ltesim.password)
        for p in process_list:
            p.start()
        for p in process_list:
            p.join()



    def _collect_node_log(self, ip, name, nodetype):
        logdir = os.getcwd()
        with pmoshell(ip, name, nodetype) as p:
            info('Collecting logs on node: {}'.format(name))
            p.logfile_read = sys.stdout
            dcg_cmd = 'dcgm {}'.format(logdir)
            if nodetype == 'G2':
                dcg_cmd = 'dcgm -k 1 {}'.format(logdir)
            p.sendline(dcg_cmd)
            p.expect(MOSHELL_PROMPT, timeout=1800)
            info('Log collection done on node: {}. Please check!'.format(name))
            

    def _collect_uctool_log(self, ip, name, usrname, passwd):
        src_dir = None
        with pssh(ip, name, usrname, passwd) as p:
            p.logfile_read = sys.stdout
            p.sendline('cat /uctool/{}/log/last_used_udplogger_log_directory'.format(name))
            p.expect(SSH_PROMPT)
            print(p.before)
            m = re.search('\n(/.+?)\s+', p.before)
            src_dir = m.group(1)
            
        dest_dir = os.getcwd()
        cmd = 'scp -r {}@{}:{} {}'.format(usrname, ip, src_dir, dest_dir)
        print(cmd)
        with pexec(cmd, passwd):
            info('Latest log on uctool: {} is downloaded!'.format(name))


    def _collect_ltesim_log(self, ip, name, usrname, passwd):
        src_dir = None
        with pssh(ip, name, usrname, passwd) as p:
            p.logfile_read = sys.stdout
            p.sendline('ls -t /tmp/ltesim_conf/* | head -1 | xargs egrep logger_file_pattern')
            p.expect(SSH_PROMPT)
            m = re.search('\n.*logger_file_pattern">(.+?)/\[', p.before)
            src_dir = m.group(1)
            
        dest_dir = os.getcwd()
        cmd = 'scp -r {}@{}:{} {}'.format(usrname, ip, src_dir, dest_dir)
        print(cmd)
        with pexec(cmd, passwd):
            info('Latest log on ltesim: {} is downloaded!'.format(name))

    @service
    def collect_logs(self, node_list, ltesim, **kwargs):
        process_list = []
        for node in node_list:
            is_to_collect = ask_yes_or_no(
                "Do you want to collect dcgm logs on node: {}".format(node.node_name))
            if is_to_collect:
                p = Process(
                    target=self._collect_node_log,
                    args=(node.node_ip, node.node_name, node.node_type)
                )
                process_list.append(p)

            is_to_collect = ask_yes_or_no(
                "Do you want to collect latest logs on uctool: {}".format(node.uctool_name))
            if is_to_collect:
                p = Process(
                    target=self._collect_uctool_log,
                    args=(node.uctool_ip, node.uctool_name, node.uctool_username, node.uctool_password)
                )
                process_list.append(p)


        is_to_collect = ask_yes_or_no(
            "Do you want to collect latest logs on ltesim: {}".format(ltesim.name))
        if is_to_collect:
            p = Process(
                target=self._collect_ltesim_log,
                args=(ltesim.ip, ltesim.name, ltesim.username, ltesim.password)
            )
            process_list.append(p)

        for p in process_list:
            p.start()
        for p in process_list:
            p.join()        


##########################
# Application Main 
#########################
if __name__ == '__main__':

    arg_parser = ArgumentParser()
    obj_type_list = ['ltesim', 'uctool', 'node']
    arg_parser.add_argument(
        '-t', dest='obj_type', default=None, choices=obj_type_list)
    arg_parser.add_argument('-o', dest='obj_to_operate', default=None)

    arg_parser.add_argument('-f', dest='cfg_file', nargs='?')
    arg_parser.add_argument(
        '-s',
        dest='services',
        nargs='+',
        choices=Services._registered_services)

    cli_args = arg_parser.parse_args()
    obj_to_operate = cli_args.obj_to_operate
    obj_type = cli_args.obj_type

    cfg = parse_cfg(cli_args.cfg_file)
    enb_list = cfg.enodeb_cfg_list
    ltesim = cfg.ltesim_cfg

    serv = Services()
    if obj_to_operate == None:
        for service_name in cli_args.services:
            getattr(serv, service_name)(
                enb_list, ltesim, filename=os.path.abspath(cli_args.cfg_file))
    # support start_operation() to call the main script itself in new terminal
    else:
        if obj_type == 'ltesim':
            if obj_to_operate == ltesim.name:
                serv._login_ltesim(ltesim.name, ltesim.ip, ltesim.username,
                                   ltesim.password)
        elif obj_type == 'uctool':
            for node in enb_list:
                if obj_to_operate == node.uctool_name:
                    serv._login_uctool(node.uctool_name, node.uctool_ip,
                                       node.uctool_username,
                                       node.uctool_password)
        elif obj_type == 'node':
            for node in enb_list:
                if obj_to_operate == node.node_name:
                    serv._login_node(node.node_name, node.node_ip,
                                     node.node_type)
