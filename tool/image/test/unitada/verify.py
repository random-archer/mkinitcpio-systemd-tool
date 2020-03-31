#!/usr/bin/env python

#
# verification script
#

import os
import sys
import time

this_dir = os.path.dirname(os.path.abspath(__file__))

# import shared config
project_root = os.popen("git rev-parse --show-toplevel").read().strip()
python_module = f"{project_root}/tool/module"
sys.path.insert(0, python_module)
from arkon_config import machine_unitada, Machine

machine = Machine(machine_unitada, this_dir)

machine.install_tool()

machine.service_enable_list([
    "root-entry.mount",
    "initrd-util-usb-hcd.service",
])

machine.perform_make_boot()

path_list = [

    "/etc/systemd/system/root-entry.mount",
    
    "/etc/modprobe.d/initrd-util-usb-hcd.conf",

]

link_list = [

    "/etc/systemd/system/custom-tester.target.wants/root-entry.mount",
    "/etc/systemd/system/super-duper.mount.requires/root-entry.mount",

    "/etc/systemd/system/sysinit.target.wants/initrd-util-usb-hcd.service",

]

text_list = [

    "/etc/systemd/system/root-entry.mount",

]

machine.assert_has_path_list(path_list)
machine.assert_has_link_list(link_list)
machine.assert_has_text_list(text_list)

#
# FIXME
#

# machine.booter_initiate()
# time.sleep(5)
# machine.booter_terminate()
