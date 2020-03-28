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
from arkon_config import machine_dropbear, Machine

machine = Machine(machine_dropbear, this_dir)

machine.install_tool()

machine.service_enable_list([
    "initrd-cryptsetup.path",
    "initrd-dropbear.service",
])

machine.perform_make_boot()

path_list = [

    "/usr/lib/systemd/system/initrd-cryptsetup.path",
    "/usr/lib/systemd/system/initrd-cryptsetup.service",
    "/usr/lib/systemd/system/initrd-dropbear.service",
    "/usr/lib/systemd/system/initrd-shell.service",
    "/usr/lib/systemd/system/initrd-network.service",

    "/root/.ssh/authorized_keys",
    "/usr/lib/mkinitcpio-systemd-tool/initrd-shell.sh",

    "/etc/dropbear/dropbear_ecdsa_host_key",
    "/etc/dropbear/dropbear_rsa_host_key",
    "/bin/dropbear",

]

link_list = [

    "/root/.profile",
    
    "/etc/systemd/system/sysinit.target.wants/initrd-cryptsetup.path",
    "/etc/systemd/system/sysinit.target.wants/initrd-dropbear.service",

]

text_list = [

    "/usr/lib/systemd/system/initrd-dropbear.service",
    
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
