#!/usr/bin/env python

#
# shared config for build/setup/verify cycle
#

import os
import datetime

import nspawn


# detect build system
def has_ci_azure():
    return "AZURE_EXTENSION_DIR" in os.environ


# no http proxy in azure
if has_ci_azure():
    nspawn.CONFIG['proxy']['use_host_proxy'] = 'no'
    nspawn.CONFIG['proxy']['use_machine_proxy'] = 'no'

# report state of non-bufered stdout/stderr
print(f"### PYTHONUNBUFFERED: {os.environ.get('PYTHONUNBUFFERED', None)}")

# location of machine resources
nspawn_store = nspawn.CONFIG['storage']["root"]

# location of this module
this_dir = os.path.dirname(os.path.abspath(__file__))

# arch linux archive iso image date
build_epoch = datetime.datetime(year=2020, month=3, day=1)

# current user account
host_user = os.getenv('USER', "root")

# azure or local resource location
user_home = os.getenv('HOME', "/root")

# location of source repository
project_repo = os.popen("git rev-parse --show-toplevel").read().strip()

# location of disk mount shared host/machine
# contains output of mkinitcpio: vmlinuz, linux-initramfs.img
project_boot = f"{project_repo}/boot"

# location of disk mount shared host/machine
# contains extracted content of linux-initramfs.img
project_data = f"{project_repo}/data"

# location of sysroot produced by this tool (with azure cache)
media_store = f"{nspawn_store}/resource/media"

# location of images produced by this tool (with azure cache)
image_store = f"{nspawn_store}/resource/image"

#
# container definitions
#

# image base for unit test
base_machine = "arch-base"
base_image_path = f"{image_store}/{base_machine}/default.tar.gz"
base_image_url = f"file://localhost/{base_image_path}"

# unit test: cryptsetup
cryptsetup_machine = "test-cryptsetup"
cryptsetup_image_path = f"{image_store}/{cryptsetup_machine}/default.tar.gz"
cryptsetup_image_url = f"file://localhost/{cryptsetup_image_path}"

# unit test: dropbear
dropbear_machine = "test-dropbear"
dropbear_image_path = f"{image_store}/{dropbear_machine}/default.tar.gz"
dropbear_image_url = f"file://localhost/{dropbear_image_path}"

# unit test: tinysshd
tinysshd_machine = "test-tinysshd"
tinysshd_image_path = f"{image_store}/{tinysshd_machine}/default.tar.gz"
tinysshd_image_url = f"file://localhost/{tinysshd_image_path}"

# unit test: nftables
nftables_machine = "test-nftables"
nftables_image_path = f"{image_store}/{nftables_machine}/default.tar.gz"
nftables_image_url = f"file://localhost/{nftables_image_path}"

# unit test: anything else
unitada_machine = "test-unitada"
unitada_image_path = f"{image_store}/{unitada_machine}/default.tar.gz"
unitada_image_url = f"file://localhost/{unitada_image_path}"
