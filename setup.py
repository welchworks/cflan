#!/usr/bin/env python
# steven@makeitwork.cloud
# https://github.com/welchworks/cflan/blob/main/setup.py
# setup.py - Creates NetworkManager dispatcher script

import os
import sys
import shutil

if os.getuid() != 0:
    sys.exit("Must run as root")

shutil.copyfile('set_dns.py', '/etc/NetworkManager/dispatcher.d/set_dns')
shutil.copyfile('sops_vars.yaml', '/sops_vars.yaml')
os.chown('/etc/NetworkManager/dispatcher.d/set_dns', 0, 0)
os.chown('/sops_vars.yaml', 0, 0)
os.chmod('/etc/NetworkManager/dispatcher.d/set_dns', 0o700)
os.chmod('/sops_vars.yaml', 0o600)
