#!/app/vbuild/SLED11-x86_64/python/2.7.10/bin/python -u

import os
import subprocess
from argparse import ArgumentParser
import glob

from simple_logger import *

ap = ArgumentParser()
ap.add_argument('-d', dest='destdir')
args = ap.parse_args()
dest_dir = args.destdir


exec_cmd = "cdae {}".format(os.path.join(dest_dir, "cm_*gz"))
info("Decoding dsp dump by: {}".format(exec_cmd))
pp = subprocess.Popen(exec_cmd, shell=True)
pp.communicate()

for pmd_file in glob.glob(os.path.join(dest_dir, "pmd-*gz")):
    exec_cmd = "pmd2html {} -o {}".format(pmd_file, dest_dir)
    info("Decoding pmd by: {}".format(exec_cmd))
    pp = subprocess.Popen(exec_cmd, shell=True)
    pp.communicate()

