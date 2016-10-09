#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python

import sys
import os
import subprocess
from multiprocessing import Process
from argparse import ArgumentParser
import pexpect
import time
import re

from config_parser import parse_cfg
from simple_logger import info, warning, error, blue, red

MOSHELL = "/app/moshell/latest/moshell/moshell"
MOSHELL_G2_ARGS = 'comcli=21,username=expert,password=expert'
MOSHELL2 = "{} -v '{}'".format(MOSHELL, MOSHELL_G2_ARGS)

MOSHELL_ROBOT_PROMPT = "ROBOT:="
MOSHELL_ROBOT_CFG = 'set_window_title=0,prompt_highlight=0,show_colors=0,prompt_colors=0,prompt={}'.format(
    MOSHELL_ROBOT_PROMPT)

MOSHELL_ROBOT1 = "{} -v '{}'".format(MOSHELL, MOSHELL_ROBOT_CFG)
MOSHELL_ROBOT2 = "{} -v '{},{}'".format(MOSHELL, MOSHELL_G2_ARGS,
                                        MOSHELL_ROBOT_CFG)


class ServicesRegistery(object):
    def __get__(self, obj, cls):

        if (cls == None and obj == None):
            raise AttributeError
        attr_list = dir(cls)
        if (obj != None):
            attr_list = dir(type(obj))

        service_name_list = []
        for attrname in attr_list:
            if attrname.startswith('_'):
                continue
            if (callable(getattr(cls, attrname))):
                service_name_list.append(attrname)

        return service_name_list


def service(func):
    def _service(*args, **kwargs):
        info("Staring service: {}".format(func.func_name))
        ret = func(*args, **kwargs)
        info("Service {} is done!".format(func.func_name))
        return ret

    return _service


class Services(object):

    _registered_services = ServicesRegistery()
    _uctool_prompt = ":[0-9a-zA-Z_\-/~.]+> \Z"
    _ltesim_prompt = ":[0-9a-zA-Z_\-/~.]+> \Z"
    _moshell_prompt = "{}> \Z".format(MOSHELL_ROBOT_PROMPT)

    _win_size = (50, 180)

    def _do_actions(self, p, action_sequence, prompt):
        for act in action_sequence:
            p.sendline(act)
            p.expect(prompt)


    def _login_node(self, node_name, node_ip, node_type='G1'):
        """
        moshell to node and leave it in interactive mode
        """

        info("moshell to " + node_name)
        moshell_cli = MOSHELL if node_type == 'G1' else MOSHELL2
        exec_cmd = "{} {}".format(moshell_cli, node_ip)
        p = pexpect.spawn(exec_cmd, dimensions=self._win_size)
        p.logfile_read = sys.stdout
        p.expect(".*> ")
        p.sendline('lt all')
        p.logfile_read = None
        p.interact()

    def _login_uctool(self, name, ip, usrname, passwd):
        """
        ssh to uctool server and leave it in interactive mode
        """

        info("ssh to " + name)
        exec_cmd = "ssh {}@{}".format(usrname, ip)
        p = pexpect.spawn(exec_cmd, dimensions=self._win_size)
        p.logfile_read = sys.stdout
        p.expect("Password: ")
        p.sendline(passwd)
        p.expect(self._uctool_prompt)

        action_sequence = ["cd /uctool/{}/bin".format(name),
                           "./uctool.sh info"]
        self._do_actions(p, action_sequence, self._uctool_prompt)
        p.logfile_read = None
        p.interact()

    def _login_ltesim(self, name, ip, usrname, passwd):
        """
        ssh to ltesim server and leave it in interactive mode
        """

        info("ssh to " + name)
        exec_cmd = "ssh {}@{}".format(usrname, ip)
        p = pexpect.spawn(exec_cmd, dimensions=self._win_size)
        p.logfile_read = sys.stdout
        p.expect("Password: ")
        p.sendline(passwd)
        p.expect(self._ltesim_prompt)

        action_sequence = ["rpm -qa | egrep 'ltesim|lctool'"]
        self._do_actions(p, action_sequence, self._ltesim_prompt)
        p.logfile_read = None
        p.interact()

    def _ask_yes_or_no(self, prompt):
        while (True):
            valid_answers = ['y', 'n']
            is_save_cv = raw_input(blue("{} [y/n] ? ".format(prompt)))
            if is_save_cv in valid_answers:
                return True if is_save_cv == 'y' else False

    def _run_mo_actions(self, moshell_cmd, action_sequence):
        """
        run moshell commands sequentially 
        """

        p = pexpect.spawn(moshell_cmd, timeout=900)
        p.logfile_read = sys.stdout
        p.expect(self._moshell_prompt)

        for action in action_sequence:
            p.sendline(action)
            i = p.expect([self._moshell_prompt, '\[y/n\] \? '])
            if i == 1:
                p.sendline('y')
                p.expect(self._moshell_prompt)

        p.close()

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

        action_sequence = [
            'lt all',
            'cvset {}'.format(cv_name), 
            'confbld+',
            'accn 0 manualRestart 2 0 0', 
            'pol'
        ]

        if node_type == 'G2':
            action_sequence = [
                'lt all', 
                'cvre {}'.format(cv_name)
            ]

        if is_save_cv:
            saved_cvname = 'Created_By_Test_Script'
            extra_actions = ['cvrm {}'.format(saved_cvname), 
                             'cvmk {}'.format(saved_cvname)]
            action_sequence = extra_actions + action_sequence

        moshell_cli = MOSHELL_ROBOT1 if node_type == 'G1' else MOSHELL_ROBOT2
        self._run_mo_actions('{} {}'.format(moshell_cli, node_ip),
                             action_sequence)
        info("CV is set and restart done on node: {}".format(node_name))

    def _install_uctool(self, ip, name, release, revision, usrname, passwd):
        info("Start to install software on uctool: {}".format(name))
        exec_cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --uctool {rel} {rev} --user {usrname} --server {ip} --uctoolnames "{name}" uctoolinstall'.format(
            rel=release, rev=revision, usrname=usrname, ip=ip, name=name)

        p = pexpect.spawn(exec_cmd)
        p.logfile_read = sys.stdout
        p.expect('Password: ')
        p.sendline(passwd)
        p.expect(pexpect.EOF, timeout=120)
        info("Installation done on uctool: {}".format(name))
        p.logfile_read = None
        p.close()

    def _install_ltesim(self, ip, name, revision, usrname, passwd):
        info("Start to install software on ltesim: {}".format(name))
        exec_cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --ltesim {rev} --user {usrname} --server {ip} rpminstall'.format(
            rev=revision, usrname=usrname, ip=ip)

        p = pexpect.spawn(exec_cmd)
        p.logfile_read = sys.stdout
        p.expect('Password: ')
        p.sendline(passwd)
        p.expect(pexpect.EOF, timeout=120)
        info("Installation done on ltesim: {}".format(name))
        p.logfile_read = None
        p.close()

    @service
    def set_baseline(self, node_list, ltesim, **kwargs):
        process_list = []

        doit = self._ask_yes_or_no("Install '{}' on ltesim: {}".format(
            ltesim.revision, ltesim.name))
        if doit:
            p = Process(
                target=self._install_ltesim,
                args=(ltesim.ip, ltesim.name, ltesim.revision, ltesim.username,
                      ltesim.password))
            process_list.append(p)

        for node in node_list:
            doit = self._ask_yes_or_no(
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

            doit = self._ask_yes_or_no("Set cv '{}' on node: {}".format(
                node.node_cv, node.node_name))

            if doit:
                is_save_cv = self._ask_yes_or_no("Do you want to save a cv first on node: {}".format(node.node_name))
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
        1. stop uctool
        2. cold restart node
        3. block uctool cells
        4. restart uctool and wait for CELL_SETUP in log 
        5. deblock uctool cells
        """
        info("Login to {} and {}".format(node_name, uctool_name))
        moshell_cli = MOSHELL_ROBOT1 if node_type == 'G1' else MOSHELL_ROBOT2
        moshell_cmd = '{} {}'.format(moshell_cli, node_ip)
        pnode = pexpect.spawn(moshell_cmd, timeout=360)
        pnode.expect(self._moshell_prompt)
        pnode.logfile_read = sys.stdout
        action_sequence = ["lt all",
                           "ma simcells cell simulated true"]
#        action_sequence.append("mr simcells cell administ 0")
        self._do_actions(pnode, action_sequence, self._moshell_prompt)

        puctool = pexpect.spawn(
            'ssh {}@{}'.format(usrname, uctool_ip), timeout=300)
        puctool.expect('Password: ')
        puctool.sendline(passwd)
        puctool.expect(self._uctool_prompt)
        puctool.logfile_read = sys.stdout

        info("Stopping uctool: {}".format(uctool_name))
        action_sequence = ["cd /uctool/{}/bin".format(uctool_name),
                           "./uctool.sh stop"]
        self._do_actions(puctool, action_sequence, self._uctool_prompt)
        sleep_time = 60
        info("Waiting for {} seconds before continue".format(sleep_time))
        time.sleep(sleep_time)
        
        info("Cold restarting the node: {}".format(node_name))
        restart_cmd = "accn 0 manualRestart 2 0 0" if node_type == 'G1' else "accn FieldReplaceableUnit=1$ restartUnit 1 0 0"
        action_sequence = ["lt all", "confbld+", restart_cmd, "pol 10 60"]
        self._do_actions(pnode, action_sequence, self._moshell_prompt)


        info("Blocking simulated cells on node: {}".format(node_name))
        action_sequence = ["st simcells",
                           "wait 120",
                           "bl simcells",
                           "wait 60",
                           "st simcells"]
        self._do_actions(pnode, action_sequence, self._moshell_prompt)

        info("Restartng uctool: {}".format(uctool_name))     
        puctool.sendline('./uctool.sh restart')
        puctool.expect(self._uctool_prompt)
        m = re.search("udplogger.sh: (.+?/udplogger.log) created", puctool.before)
        uctool_logfile = m.group(1)
        search_keywords = 'WAITING_FOR_CELL_SETUP'
        for i in range(30):
            time.sleep(10)
            info("searching {} in {}".format(search_keywords, uctool_logfile))
            puctool.sendline('grep {} {}'.format(search_keywords,uctool_logfile))
            puctool.expect(self._uctool_prompt)
            m = re.search(search_keywords, puctool.before)
            if m != None:
                info("{} found in {}!".format(search_keywords, uctool_logfile))
                break
            if i == 5:
                raise RuntimeError(red("Timeout waiting for CELL_SETUP on uctool {}".format(uctool_name)))
        sleep_time = 60
        info("Waiting for {} seconds before continue".format(sleep_time))
        time.sleep(sleep_time)

        info("Deblocking simulated cells on node: {}".format(node_name))
        action_sequence = ["deb simcells", "wait 120", "st simcells"]
        self._do_actions(pnode, action_sequence, self._moshell_prompt)
        time.sleep(1)
        puctool.close()
        pnode.close()

    @service
    def run_recovery(self, node_list, *args, **kwargs):
        process_list = []
        for node in node_list:
            is_do_recovery = self._ask_yes_or_no(
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
        for p in process_list:
            p.start()
        for p in process_list:
            p.join()


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
