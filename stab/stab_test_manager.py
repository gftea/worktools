#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python

import sys
import os
import subprocess
from multiprocessing import Process
from argparse import ArgumentParser
import pexpect

from config_parser import parse_cfg
from simple_logger import info, warning, error

MOSHELL = "/app/moshell/latest/moshell/moshell"
MOSHELL_G2_ARGS = 'comcli=21,username=expert,password=expert'
MOSHELL2 = "{} -v '{}'".format(MOSHELL, MOSHELL_G2_ARGS)

MOSHELL_ROBOT_PROMPT = "ROBOT"
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

    def _login_node(self, node_name, node_ip, node_type='G1'):
        """
        moshell to node and leave it in interactive mode
        """
        info("moshell to " + node_name)
        moshell_cli = MOSHELL if node_type == 'G1' else MOSHELL2
        exec_cmd = "{} {}".format(moshell_cli, node_ip)
        p = pexpect.spawn(exec_cmd)
        p.expect(".*> ")
        p.sendline('lt all')
        p.setwinsize(50, 180)
        p.interact()

    def _login_uctool(self, name, ip, usrname, passwd):
        """
        ssh to uctool server and leave it in interactive mode
        """
        prompt = ":.+> "
        info("ssh to " + name)

        p = pexpect.spawn("ssh {}@{}".format(usrname, ip))
        p.expect("Password: ")
        p.sendline(passwd)
        p.expect(prompt)

        action_sequence = ["cd /uctool/{}/bin".format(name),
                           "./uctool.sh info"]
        p.logfile = sys.stdout
        for act in action_sequence:
            p.sendline(act)
            p.expect(prompt)
        p.logfile = None
        p.setwinsize(50, 180)
        p.interact()

    def _login_ltesim(self, name, ip, usrname, passwd):
        """
        ssh to ltesim server and leave it in interactive mode
        """
        prompt = ":.+> "
        info("ssh to " + name)

        p = pexpect.spawn("ssh {}@{}".format(usrname, ip))
        p.expect("Password: ")
        p.sendline(passwd)
        p.expect(prompt)

        p.logfile = sys.stdout
        p.sendline("rpm -qa | egrep 'ltesim|lctool'")
        p.expect(prompt)
        p.logfile = None
        p.setwinsize(50, 180)
        p.interact()

    def _ask_yes_or_no(self, prompt):
        while (True):
            valid_answers = ['y', 'n']
            is_save_cv = raw_input("{} [y/n] ? ".format(prompt))
            if is_save_cv in valid_answers:
                return True if is_save_cv == 'y' else False

    def _run_mo_actions(self, moshell_cmd, action_sequence):
        """
        run moshell commands sequentially 
        """

        moshell_prompt = "{}> ".format(MOSHELL_ROBOT_PROMPT)
        p = pexpect.spawn(moshell_cmd)
        p.logfile = sys.stdout
        p.expect(moshell_prompt)

        for action, tmo in action_sequence:
            p.sendline(action)
            i = p.expect([moshell_prompt, '\[y/n\] \? '], timeout=tmo)
            if i == 1:
                p.sendline('y')
                p.expect(moshell_prompt, timeout=tmo)
        p.logfile = None
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
            ('lt all', 60), ('cvset {}'.format(cv_name), 10), ('confbld+', 10),
            ('accn 0 manualRestart 2 0 0', 10), ('pol', 300)
        ]

        if node_type == 'G2':
            action_sequence = [
                ('lt all', 60), ('cvre {}'.format(cv_name), 300)
            ]

        if is_save_cv:
            action_sequence.insert(0, ('cvmk Created_By_Test_Script', 60))

        moshell_cli = MOSHELL_ROBOT1 if node_type == 'G1' else MOSHELL_ROBOT2
        self._run_mo_actions('{} {}'.format(moshell_cli, node_ip),
                             action_sequence)
        info("CV is set and restart done on node: {}".format(node_name))

    def _install_uctool(self, ip, name, release, revision, usrname, passwd):
        info("Start to install software on uctool: {}".format(name))
        exec_cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --uctool {rel} {rev} --user {usrname} --server {ip} --uctoolnames "{name}" uctoolinstall'.format(
            rel=release, rev=revision, usrname=usrname, ip=ip, name=name)

        p = pexpect.spawn(exec_cmd)
        p.logfile = sys.stdout
        p.expect('Password: ')
        p.sendline(passwd)
        p.expect(pexpect.EOF, timeout=120)
        info("Installation done on uctool: {}".format(name))
        p.logfile = None
        p.close()

    def _install_ltesim(self, ip, name, revision, usrname, passwd):
        info("Start to install software on ltesim: {}".format(name))
        exec_cmd = '/proj/stab_lmr/tools/LTEsim/latest/rpm_installer.sh --ltesim {rev} --user {usrname} --server {ip} rpminstall'.format(
            rev=revision, usrname=usrname, ip=ip)

        p = pexpect.spawn(exec_cmd)
        p.logfile = sys.stdout
        p.expect('Password: ')
        p.sendline(passwd)
        p.expect(pexpect.EOF, timeout=120)
        info("Installation done on ltesim: {}".format(name))
        p.logfile = None
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
                is_save_cv = self._ask_yes_or_no("Do you want to save a cv")
                p = Process(
                    target=self._set_cv_and_restart,
                    args=(node.node_ip, node.node_cv, node.node_type,
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
        subprocess.Popen(exec_cmd, shell=True)

        for node in node_list:
            exec_cmd = 'gnome-terminal --geometry=180x50+30+30 -t {name} -e "python {script} -t uctool -f {fname} -o {name}"'.format(
                script=main_script, name=node.uctool_name, fname=filename)
            subprocess.Popen(exec_cmd, shell=True)

            exec_cmd = 'gnome-terminal --geometry=180x50+30+30 -t {name} -e "python {script} -t node -f {fname} -o {name}"'.format(
                script=main_script, name=node.node_name, fname=filename)
            subprocess.Popen(exec_cmd, shell=True)


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
