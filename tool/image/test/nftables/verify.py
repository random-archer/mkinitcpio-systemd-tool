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
from arkon_config import kernel_version
from arkon_config import nftables_machine
from machine_unit import MachineUnit

machine = MachineUnit(nftables_machine, this_dir)

machine.install_this_tool()

machine.service_enable_list([

    "initrd-cryptsetup.path",
    "initrd-tinysshd.service",
    "initrd-nftables.service",

    "initrd-emergency.target",
    "initrd-debug-progs.service",
    "initrd-sysroot-mount.service",

])

machine.perform_make_boot()

path_list = [

    "/usr/lib/systemd/system/initrd-cryptsetup.path",
    "/usr/lib/systemd/system/initrd-cryptsetup.service",
    "/usr/lib/systemd/system/initrd-tinysshd.service",
    "/usr/lib/systemd/system/initrd-network.service",
    "/usr/lib/systemd/system/initrd-shell.service",

    f"/usr/lib/modules/{kernel_version}/kernel/dm-crypt.ko",

    "/etc/nftables.conf",
    "/usr/bin/nft",
    "/usr/lib/systemd/system/initrd-nftables.service",
    f"/usr/lib/modules/{kernel_version}/kernel/nf_tables.ko",
    f"/usr/lib/modules/{kernel_version}/kernel/nft_socket.ko",

]

link_list = [

    "/root/.profile",

    "/etc/systemd/system/sysinit.target.wants/initrd-cryptsetup.path",
    "/etc/systemd/system/sysinit.target.wants/initrd-debug-progs.service",

    "/etc/systemd/system/initrd-root-fs.target.wants/initrd-sysroot-mount.service",

    "/etc/systemd/system/sysinit.target.wants/initrd-tinysshd.service",

    "/etc/systemd/system/initrd-network.service.wants/initrd-nftables.service",

]

text_list = [

    # TODO add texts to assert

]

machine.assert_has_path_list(path_list)
machine.assert_has_link_list(link_list)
machine.assert_has_text_list(text_list)

#
# FIXME implement full test
#

machine.booter_qemu_initiate()
time.sleep(5)
machine.booter_qemu_terminate()
