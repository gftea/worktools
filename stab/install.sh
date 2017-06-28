#!/bin/sh

python -m ensurepip -v --user
~/.local/bin/pip install -r requirements.txt -f /proj/stab_lmr/users/ekaiqch/tools/worktools --disable-pip-version-check -v --user

