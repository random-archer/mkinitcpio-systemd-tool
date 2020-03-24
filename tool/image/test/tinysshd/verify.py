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
from arkon_config import machine_tinysshd, Machine

machine = Machine(machine_tinysshd, this_dir)

machine.install_tool()

machine.service_enable_list([
    "initrd-cryptsetup.path",
    "initrd-tinysshd.service",
])

machine.produce_boot_result()

path_list = [

    "/root/.ssh/authorized_keys",
    "/usr/lib/mkinitcpio-systemd-tool/initrd-shell.sh",

    "/etc/tinyssh/sshkeydir/.ed25519.sk",
    "/etc/tinyssh/sshkeydir/ed25519.pk",
    "/bin/busybox",
    "/bin/tinysshd",

    "/usr/lib/systemd/system/initrd-tinysshd.service",
    "/usr/lib/systemd/system/initrd-network.service",
    "/usr/lib/systemd/system/initrd-shell.service",
    "/usr/lib/systemd/system/initrd-cryptsetup.path",
    "/usr/lib/systemd/system/initrd-cryptsetup.service",

]

link_list = [

    "/root/.profile",

    "/etc/systemd/system/sysinit.target.wants/initrd-cryptsetup.path",
    "/etc/systemd/system/sysinit.target.wants/initrd-tinysshd.service",

]

text_list = [

    "/usr/lib/systemd/system/initrd-tinysshd.service",

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