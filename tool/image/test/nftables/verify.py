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
from arkon_config import nftables_machine
from machine_unit import MachineUnit

machine = MachineUnit(nftables_machine, this_dir)

machine.install_this_tool()

machine.service_enable_list([

    # TODO add services to enable

    "initrd-cryptsetup.path",
    "initrd-tinysshd.service",
    "initrd-nftables.service",

    "initrd-emergency.target",
    "initrd-debug-progs.service",
    "initrd-sysroot-mount.service",

])

machine.perform_make_boot()

path_list = [
    # TODO add paths to assert
]

link_list = [
    # TODO add links to assert
]

text_list = [
    # TODO add texts to assert
]

machine.assert_has_path_list(path_list)
machine.assert_has_link_list(link_list)
machine.assert_has_text_list(text_list)


machine.booter_qemu_initiate()

# wait for quemo start
# TODO use wait-for-condition
time.sleep(5)

# FIXME add tests agains qemu instance, i.e. try netcat vs firewall

machine.booter_qemu_terminate()
