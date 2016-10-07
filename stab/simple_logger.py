import logging 


RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'
ENDC = '\033[0m'


def green():
    return {'color_start':GREEN, 'color_end':ENDC}

def blue():
    return {'color_start':BLUE, 'color_end':ENDC}

def yellow():
    return {'color_start':YELLOW, 'color_end':ENDC}

def red():
    return {'color_start':RED, 'color_end':ENDC}


fmt = "%(color_start)s%(levelname)s: %(message)s%(color_end)s"
logging.basicConfig(level=logging.INFO, format=fmt)

def info(msg):
    logging.info(msg, extra=green())

def warning(msg):
    logging.warning(msg, extra=yellow())

def error(msg):
    logging.warning(msg, extra=red())



