from contextlib import contextmanager
from const import *
from simple_logger import *
import pexpect
import sys

def service(func):
    def _service(*args, **kwargs):
        info("========= Staring service:: '{}' =========".format(func.func_name))
        ret = func(*args, **kwargs)
        info("========= Service '{}' is done! =========".format(func.func_name))
        return ret

    return _service

def ask_yes_or_no(prompt):
    while (True):
        valid_answers = ['y', 'n']
        ans = raw_input(blue("{} [y/n] ? ".format(prompt)))
        if ans.strip() in valid_answers:
            return True if ans == 'y' else False


@contextmanager
def pexec(cmd, passwd=None):
    info("Execute command: {}".format(cmd))
    p = pexpect.spawn(cmd, timeout=1800)
    p.logfile_read = sys.stdout
    if passwd != None:
        p.expect('[pP]assword: ', timeout=30)
        p.sendline(passwd)
    p.expect(pexpect.EOF)

    yield p

    p.logfile = None
    p.logfile_read = None
    p.logfile_send = None   
    p.close()

@contextmanager
def pssh(ip, name, usrname, passwd, is_interact=False):
    # __enter__
    info("ssh to " + name)
    exec_cmd = "ssh {}@{}".format(usrname, ip)
    p = pexpect.spawn(exec_cmd, timeout=1800, dimensions=TTY_WIN_SIZE)
    p.expect("Password: ", timeout=30)
    p.sendline(passwd)
    p.expect(SSH_PROMPT, timeout=30)
    
    yield p

    #__exit__
    p.logfile = None
    p.logfile_read = None
    p.logfile_send = None
    if is_interact:
        p.interact(escape_character=None)
    else:
        p.close()

@contextmanager
def pssh2(ip, usrname, passwd, prompt=SSH_PROMPT):
    # __enter__
    info("ssh to " + ip)
    exec_cmd = "ssh {}@{}".format(usrname, ip)
    p = pexpect.spawn(exec_cmd, timeout=1800, dimensions=TTY_WIN_SIZE)

    ret = p.expect(["connecting (yes/no)?", "[pP]assword: "], timeout=30)
    if ret == 0:
        p.sendline('yes')
        p.expect("[pP]assword: ", timeout=30)            
    p.sendline(passwd)
    p.expect(prompt)

    yield p

    #__exit__
    p.logfile = None
    p.logfile_read = None
    p.logfile_send = None
    p.close()




@contextmanager
def pmoshell(ip, name, nodetype, is_interact=False):
    info("moshell to " + name)
    if is_interact:
        moshell_cli = MOSHELL if nodetype == 'G1' else MOSHELL2
        prompt = ".*> "
    else:
        moshell_cli = MOSHELL_ROBOT1 if nodetype == 'G1' else MOSHELL_ROBOT2
        prompt = MOSHELL_PROMPT
    exec_cmd = '{} {}'.format(moshell_cli, ip)
    p = pexpect.spawn(exec_cmd, timeout=1800, dimensions=TTY_WIN_SIZE)
    p.expect(prompt, timeout=30)

    yield p

    p.logfile = None
    p.logfile_read = None
    p.logfile_send = None
    if is_interact:
        p.interact(escape_character=None)
    else:
        p.close()    
    
    

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


class ServicesRegistery2(object):

    def __get__(self, obj, cls):
        if (obj == None):
            raise AttributeError("Service registered should be called on instance")
        attr_list = dir(obj)

        service_list = []
        for attrname in attr_list:
            if attrname.startswith('_'):
                continue
            attr_obj =  getattr(obj, attrname)
            if (callable(attr_obj)):
                service_list.append(attr_obj)

        return service_list


######
#Test
######
if __name__ == '__main__':
    
    import sys
    with pssh('10.216.72.168', 'kiuctool105', 'ltelab', 'ltesimltesim', is_interact=True) as p:
        p.logfile_read = sys.stdout
        p.sendline('cd /uctool')
        p.expect(SSH_PROMPT)

    with pssh('10.216.72.168', 'kiuctool105', 'ltelab', 'ltesimltesim') as p:
        p.logfile_read = sys.stdout
        p.sendline('cd /uctool')
        p.expect(SSH_PROMPT)
        p.sendline('ls -l')
        p.expect(SSH_PROMPT)

    with pssh('10.216.72.29', 'ltesim0005', 'ltelab', 'ltesimltesim') as p:
        p.logfile_read = sys.stdout
        p.sendline('cd /tmp')
        p.expect(SSH_PROMPT)
        p.sendline('ls -l')
        p.expect(SSH_PROMPT)

    with pmoshell('10.216.60.21', 'enb1511', 'G1'):
        p.logfile_read = sys.stdout
        p.sendline('st cell')
        p.expect(MOSHELL_PROMPT)
    

    with pmoshell('10.216.60.21', 'enb1511', 'G1') as p:
        p.logfile_read = sys.stdout
        p.sendline('st cell')
        p.expect(MOSHELL_PROMPT)

    with pmoshell('10.216.60.21', 'enb1511', 'G1', is_interact=True) as p:
        p.logfile_read = sys.stdout
        prompt = ".*>"
        p.sendline('lt all')
        p.expect(prompt)
