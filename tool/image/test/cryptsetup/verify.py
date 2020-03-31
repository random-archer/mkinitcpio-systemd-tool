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
from arkon_config import machine_cryptsetup, Machine

machine = Machine(machine_cryptsetup, this_dir)

machine.install_tool()

machine.service_enable_list([

    "initrd-cryptsetup.path",

    "initrd-emergency.target",

    "initrd-debug-progs.service",

    "initrd-sysroot-mount.service",

])

machine.perform_make_boot()

path_list = [

    "/usr/lib/systemd/system/initrd-cryptsetup.path",
    "/usr/lib/systemd/system/initrd-cryptsetup.service",

    "/usr/lib/systemd/system/initrd-shell.service",

    "/usr/lib/systemd/system/initrd-sysroot-mount.service",

    "/root/.ssh/authorized_keys",
    "/usr/lib/mkinitcpio-systemd-tool/initrd-shell.sh",

    "/bin/dmsetup",
    "/bin/swapon",
    "/bin/swapoff",

    "/usr/lib/modules/5.5.6-arch1-1/kernel/dm-crypt.ko",

    "/usr/lib/udev/rules.d/10-dm.rules",
    "/usr/lib/udev/rules.d/11-dm-initramfs.rules",
    "/usr/lib/udev/rules.d/13-dm-disk.rules",
    "/usr/lib/udev/rules.d/95-dm-notify.rules",

    "/usr/lib/systemd/system/cryptsetup.target",
    "/usr/lib/systemd/system/cryptsetup-pre.target",
    "/usr/lib/systemd/systemd-cryptsetup",
    "/usr/lib/systemd/system-generators/systemd-cryptsetup-generator",
    "/usr/lib/systemd/system-generators/systemd-fstab-generator",

]

link_list = [

    "/root/.profile",

    "/etc/systemd/system/sysinit.target.wants/initrd-cryptsetup.path",
    "/etc/systemd/system/sysinit.target.wants/initrd-debug-progs.service",

    "/etc/systemd/system/initrd-root-fs.target.wants/initrd-sysroot-mount.service",

]

text_list = [

    "/etc/crypttab",
    "/etc/fstab",

    "/usr/lib/systemd/system/initrd-cryptsetup.path",
    "/usr/lib/systemd/system/initrd-cryptsetup.service",

]

machine.assert_has_path_list(path_list)
machine.assert_has_link_list(link_list)
machine.assert_has_text_list(text_list)

#
# FIXME
#

machine.booter_qemu_initiate()
time.sleep(5)
machine.booter_qemu_terminate()

# machine.booter_sysd_initiate()
# time.sleep(5)
# machine.booter_sysd_terminate()
