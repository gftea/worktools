import logging 


RED = '\033[31;1m'
GREEN = '\033[32;1m'
YELLOW = '\033[33;1m'
BLUE = '\033[34;1m'
WHITEBLACK = '\033[37;1;40m'
BLACKWHITE ='\033[30;1;47m'
ENDC = '\033[0m'


def green(s):
    return GREEN + s + ENDC

def blue(s):
    return BLUE + s + ENDC

def yellow(s):
    return YELLOW + s + ENDC 

def red(s):
    return RED + s + ENDC

def whiteblack(s):
    return WHITEBLACK + s + ENDC

def blackwhite(s):
    return BLACKWHITE + s + ENDC


GREEN_EXT = {'color_start':GREEN, 'color_end':ENDC}
BLUE_EXT = {'color_start':BLUE, 'color_end':ENDC}
YELLOW_EXT = {'color_start':YELLOW, 'color_end':ENDC}
RED_EXT = {'color_start':RED, 'color_end':ENDC}

fmt = "%(color_start)s%(levelname)s: %(message)s%(color_end)s"
logging.basicConfig(level=logging.INFO, format=fmt)

def info(msg):
    logging.info(msg, extra=GREEN_EXT)

def warning(msg):
    logging.warning(msg, extra=YELLOW_EXT)

def error(msg):
    logging.warning(msg, extra=RED_EXT)



